# pylint: disable=import-outside-toplevel
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
from robot import rebot


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
    tags=None,
    **run_parameters,
):
    assert browser in Browsers
    browser = Browsers[browser]

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

        started = arrow.utcnow()
        effective_output_dir = output_dir / str(index)
        effective_output_dir.mkdir(parents=True, exist_ok=True)
        effective_test_file = test_file

        vars_command = []
        for k, v in effective_variables.items():
            vars_command.append("--variable")
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
                ]
            )
            if tags:
                for tag in tags.split(","):
                    tag = tag.strip()
                    cmd += ["--include", tag]

            cmd += [effective_test_file]
            subprocess.run(cmd, check=True, encoding="utf8", cwd=test_file.parent)

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
    [x.start() for x in threads]  # pylint: disable=W0106
    [x.join() for x in threads]  # pylint: disable=W0106

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

        except Exception as ex:  # pylint: disable=broad-except
            logger.exception(ex)
            run_test_result = {
                "all_ok": False,
            }

        run_test_result["name"] = test_file.stem
        test_results.append(run_test_result)
        logger.info(
            ("Test finished in %s " "seconds."), run_test_result.get("duration")
        )
        collect_all_reports(test_file, output_sub_dir)

    return test_results

def collect_all_reports(test_file, parent_dir):
    """
    Directory contains directories which are numbers that indicate the amount of
    workers.
    """
    files = []
    for dir in Path(parent_dir).glob("*"):
        if not dir.is_dir():
            continue
        path = dir / 'output.xml'
        files.append(path)
    name = test_file.name.replace('.robot', '')
    with open(parent_dir / 'output.txt', 'w') as stdout:
        os.chdir(parent_dir)
        rebot(*files, name=name, log=None, stdout=stdout)
        report_html = Path("/opt/robot/report.html")
        if report_html.exists():
            shutil.move("/opt/robot/report.html", parent_dir)

def run_tests(params, test_files, token, results_file):
    """
    Call this with json request with following data:
    - params: dict passed to robottest.sh
    - archive: robot tests in zip file format
    Expects tar archive of tests files to be executed.


    """
    # setup workspace folders
    logger.info(f"Starting test with params:\n{json.dumps(params, indent=4)}")
    output_dir = Path(os.environ["OUTPUT_DIR"])
    token_dir = output_dir / token
    _clean_dir(token_dir)
    src_dir = Path("/opt/src")

    test_results = []
    test_results += _run_tests(
        params,
        map(lambda file: src_dir / file, test_files),
        token_dir,
    )

    results_file = output_dir / (results_file or 'results.json')
    results_file.write_text(json.dumps(test_results))
    uid = os.environ["OWNER_UID"]
    os.system(f"sudo chown -R {uid}:{uid} '{output_dir.parent}'")
    logger.info(f"Created output file at {results_file}")


def smoketestselenium():
    from selenium import webdriver
    from selenium.webdriver import FirefoxOptions

    opts = FirefoxOptions()
    opts.add_argument("--headless")
    try:
        browser = webdriver.Firefox(options=opts)
    except:
        log = Path('geckodriver.log')
        if log.exists():
            raise Exception(log.read_text())

    # browser.get("http://example.com")


def _clean_dir(path):
    for file in path.glob("*"):
        if file.is_dir():
            shutil.rmtree(file)
        else:
            file.unlink()

def fix_output_ownership():
    assert os.getenv("OUTPUT_DIR"), "$OUTPUT_DIR is not defined"
    subprocess.check_call("sudo chown -R robot \"$OUTPUT_DIR\"", shell=True)
    assert os.getenv("ODOO_IMAGES"), "$ODOO_IMAGES env not defined"
    subprocess.check_call([
        "rsync", os.getenv("ODOO_IMAGES") + "/",
        "/opt/robot/.odoo/images",
        "-ar"
    ])
    subprocess.check_call("sudo chown -R robot /opt/robot", shell=True)

if __name__ == "__main__":
    fix_output_ownership()
    #archive = sys.stdin.read().rstrip()
    archive = Path("/tmp/archive")
    archive = base64.b64decode(archive.read_bytes())
    data = json.loads(archive)
    del archive

    smoketestselenium()

    run_tests(**data)
    logger.info("Finished calling robotest.py")
