import base64
from copy import deepcopy
import robot
import sys
import shutil
import os
import time
from flask import redirect
import arrow
import subprocess
from flask import jsonify
from flask import make_response
from flask import Flask
from flask import render_template
from flask import url_for
from datetime import datetime
from flask import request
import json
from pathlib import Path
import threading
import logging
import tempfile
import threading
from tabulate import tabulate


FORMAT = "[%(levelname)s] %(name) -12s %(asctime)s %(message)s"
logging.basicConfig(format=FORMAT)
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger("")  # root handler

Browsers = {
    "chrome": {
        "driver": "Chrome",
        "alias": "headlesschrome",
    },
    "firefox": {
        "driver": "Firefox",
        "alias": "headlessfirefox",
    },
}


def safe_filename(name):
    for c in ":_- \\/!?#$%&*":
        name = name.replace(c, "_")
    return name


def _get_variables_file(parent_path, content, index):
    variables_conf = parent_path / f"variables.{index}.json"
    variables_conf.write_text(json.dumps(content, indent=4))
    variables_file = parent_path / f"variables_{index}.py"
    variables_file.write_text(
        """
import json
from pathlib import Path

def get_variables():
    return json.loads(Path('{path}').read_text())
""".format(
            path=variables_conf
        )
    )
    return variables_file


def safe_avg(values):
    if not values:
        return 0
    S = float(sum(values))
    return S / float(len(values))


def _run_test(
    test_file,
    output_dir,
    url,
    dbname,
    user,
    password,
    browser="firefox",
    selenium_timeout=20,
    parallel=1,
    **run_parameters,
):
    assert browser in Browsers
    browser = Browsers[browser]

    if run_parameters:
        raise NotImplementedError(run_parameters)

    if password is True:
        password = "1"  # handle limitation of settings files

    variables = {
        "SELENIUM_DELAY": 0,
        "SELENIUM_TIMEOUT": selenium_timeout,
        "ODOO_URL": url,
        "ODOO_URL_LOGIN": url + "/web/login",
        "ODOO_USER": user,
        "ODOO_PASSWORD": password,
        "ODOO_DB": dbname,
        "BROWSER": browser["alias"],
        "ALIAS": browser["alias"],
        "DRIVER": browser["driver"],
    }
    for k, v in run_parameters.items():
        variables[k] = v
    logger.info("Configuration:\n%s", variables)

    results = [
        {
            "ok": None,
            "duration": None,
        }
        for _ in range(parallel)
    ]
    threads = []

    def run_robot(index):
        effective_variables = deepcopy(variables)
        effective_variables["TEST_RUN_INDEX"] = index
        effective_variables["CURRENT_TEST"] = f"{safe_filename(test_file.stem)}_{index}"
        effective_variables["TEST_DIR"] = str(test_file.parent)

        # variables_file = _get_variables_file(
        #     test_file.parent, effective_variables, index
        # )
        started = arrow.utcnow()
        effective_output_dir = output_dir / str(index)
        effective_output_dir.mkdir(parents=True, exist_ok=True)
        effective_test_file = test_file

        vars_command = []
        for k, v in effective_variables.items():
            vars_command.append(f"--variable")
            if ":" in k:
                raise Exception(f"invalid token in {k}")
            vars_command.append(f"{k}:{v}")

        try:
            cmd = (
                [
                    "/usr/local/bin/robot",
                    "-X",  # exit on failure
                ]
                + vars_command
                + [
                    "--outputdir",
                    effective_output_dir,
                    effective_test_file,
                ]
            )
            subprocess.run(cmd, check=True, encoding="utf8", cwd='/tmp')   #  to put geckodriver.log there
        except subprocess.CalledProcessError:
            success = False
        else:
            success = True

        results[index]["ok"] = success
        results[index]["duration"] = (arrow.utcnow() - started).total_seconds()

    logger.info("Preparing threads")
    for i in range(parallel):
        t = threading.Thread(target=run_robot, args=((i,)))
        t.daemon = True
        threads.append(t)
    [x.start() for x in threads]
    [x.join() for x in threads]

    success_rate = (
        not results and 0 or len([x for x in results if x["ok"]]) / len(results) * 100
    )

    durations = list(map(lambda x: x["duration"], results))
    min_duration = durations and min(durations) or 0
    max_duration = durations and max(durations) or 0
    avg_duration = safe_avg(durations)

    any_failed = False
    for result in results:
        if not result["ok"]:
            any_failed = True

    return {
        "all_ok": not any_failed,
        "details": results,
        "count": len(list(filter(lambda x: not x is None, results))),
        "succes_rate": success_rate,
        "min_duration": min_duration,
        "max_duration": max_duration,
        "avg_duration": avg_duration,
    }


def _run_tests(params, test_files, output_dir):
    # init vars
    test_results = []

    # iterate robot files and run tests
    for test_file in test_files:
        output_sub_dir = output_dir / f"{test_file.stem}_p{params['parallel']}"

        # build robot command: pass all params from data as
        # parameters to the command call
        logger.info(
            ("Running test %s " "using output dir %s"), test_file.name, output_sub_dir
        )
        output_sub_dir.mkdir(parents=True, exist_ok=True)

        try:
            run_test_result = _run_test(
                test_file=test_file, output_dir=output_sub_dir, **params
            )

        except Exception:  # pylint: disable=broad-except
            run_test_result = {
                "all_ok": False,
            }

        run_test_result["name"] = test_file.stem
        test_results.append(run_test_result)
        logger.info(
            ("Test finished in %s " "seconds."), run_test_result.get("duration")
        )

    return test_results


def run_tests(params, test_files, token):
    """
    Call this with json request with following data:
    - params: dict passed to robottest.sh
    - archive: robot tests in zip file format
    Expects tar archive of tests files to be executed.


    """
    # setup workspace folders
    logger.info(f"Starting test with params:\n{json.dumps(params, indent=4)}")
    output_dir = Path(os.environ["OUTPUT_DIR"]) / token
    clean_dir(output_dir)
    src_dir = Path("/opt/src")

    test_results = []
    test_results += _run_tests(
        params,
        map(lambda file: src_dir / file, test_files),
        output_dir,
    )

    (output_dir / "results.json").write_text(json.dumps(test_results))
    id = os.environ["OWNER_UID"]
    os.system(f"sudo chown -R {id}:{id} '{output_dir.parent}'")


def smoketestselenium():
    from selenium import webdriver
    from selenium.webdriver import FirefoxOptions

    opts = FirefoxOptions()
    opts.add_argument("--headless")
    browser = webdriver.Firefox(options=opts)

    browser.get("http://example.com")


def clean_dir(path):
    for file in path.glob("*"):
        if file.is_dir():
            shutil.rmtree(file)
        else:
            file.unlink()


if __name__ == "__main__":
    archive = sys.stdin.read().rstrip()
    archive = base64.b64decode(archive)
    data = json.loads(archive)
    del archive

    smoketestselenium()

    run_tests(**data)
    logger.info("Finished calling robotest.py")
