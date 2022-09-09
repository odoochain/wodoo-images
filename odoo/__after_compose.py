import sys
import shutil
import json
import re
import base64
import click
import yaml
import inspect
import os
import subprocess
from pathlib import Path

dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

MINIMAL_MODULES = []  # to include its dependencies

my_cache = {}


def _get_sha(config):
    if "sha" not in my_cache:
        from wodoo.init_functions import _get_customs_root

        path = _get_customs_root(Path(os.getcwd()))
        sha = subprocess.check_output(
            ["git", "log", "-n1", "--pretty=format:%H"], cwd=str(path), encoding="utf8"
        ).strip()
        my_cache["sha"] = sha
    return my_cache["sha"]


def _setup_remote_debugging(config, yml):
    if config.devmode:
        key = "odoo"
    else:
        key = "odoo_debug"
    yml["services"][key].setdefault("ports", [])
    if config.ODOO_PYTHON_DEBUG_PORT and config.ODOO_PYTHON_DEBUG_PORT != "0":
        yml["services"][key]["ports"].append(
            f"0.0.0.0:{config.ODOO_PYTHON_DEBUG_PORT}:5678"
        )

def after_compose(config, settings, yml, globals):
    # store also in clear text the requirements

    yml["services"].pop("odoo_base")
    # odoodc = yaml.safe_load((dirs['odoo_home'] / 'images/odoo/docker-compose.yml').read_text())

    # download python3.x version
    python_tgz = (
        config.dirs["images"]
        / "odoo"
        / "python"
        / f"Python-{settings['ODOO_PYTHON_VERSION']}.tgz"
    )
    if not python_tgz.exists():
        v = settings['ODOO_PYTHON_VERSION']
        url = f"https://www.python.org/ftp/python/{v}/Python-{v}.tgz"
        click.secho(f"Downloading {url}")
        with globals['tools'].download_file(url) as filepath:
            shutil.copy(filepath, python_tgz)

    PYTHON_VERSION = tuple([int(x) for x in config.ODOO_PYTHON_VERSION.split(".")])

    # Add remote debugging possibility in devmode
    _setup_remote_debugging(config, yml)

    _determine_requirements(config, yml, PYTHON_VERSION, settings, globals)


def _determine_requirements(config, yml, PYTHON_VERSION, settings, globals):
    if float(config.ODOO_VERSION) < 13.0:
        return

    get_services = globals["tools"].get_services

    odoo_machines = get_services(config, "odoo_base", yml=yml)

    external_dependencies = _get_cached_dependencies(config, globals, PYTHON_VERSION)

    sha = _get_sha(config) if settings["SHA_IN_DOCKER"] == "1" else "n/a"
    click.secho(f"Identified SHA '{sha}'", fg="yellow")
    for odoo_machine in odoo_machines:
        service = yml["services"][odoo_machine]
        py_deps = external_dependencies["pip"]
        if "build" not in service:
            continue
        service["build"].setdefault("args", [])
        service["build"]["args"]["ODOO_REQUIREMENTS"] = base64.encodebytes(
            "\n".join(py_deps).encode("utf-8")
        ).decode("utf-8")
        service["build"]["args"]["ODOO_REQUIREMENTS_CLEARTEXT"] = (
            ";".join(py_deps).encode("utf-8")
        ).decode("utf-8")
        service["build"]["args"]["ODOO_DEB_REQUIREMENTS"] = base64.encodebytes(
            "\n".join(sorted(external_dependencies["deb"])).encode("utf-8")
        ).decode("utf-8")
        service["build"]["args"]["ODOO_FRAMEWORK_REQUIREMENTS"] = base64.encodebytes(
            (config.dirs["odoo_home"] / "requirements.txt").read_bytes()
        ).decode("utf-8")
        service["build"]["args"]["CUSTOMS_SHA"] = sha
        service["build"]["args"]["ODOO_PYTHON_VERSION"] = settings[
            "ODOO_PYTHON_VERSION"
        ]

    config.files["native_collected_requirements_from_modules"].parent.mkdir(
        exist_ok=True, parents=True
    )
    config.files["native_collected_requirements_from_modules"].write_text(
        "\n".join(external_dependencies["pip"])
    )

    # put the collected requirements into project root
    req_file = config.WORKING_DIR / "requirements.txt"
    req_file.write_text("\n".join(external_dependencies["pip"]))


def _dir_dirty(globals):
    from wodoo.odoo_config import customs_dir
    tools = globals["tools"]
    return not tools.is_git_clean(customs_dir(), ignore_files=["requirements.txt"])


def all_submodules_checked_out():
    from gimera import gimera

    try:
        gimera._check_all_submodules_initialized()
    except:
        return False
    else:
        return True


def cache_dir(tools):
    path = Path(os.path.expanduser("~/.cache/wodoo_image_odoo"))
    path.mkdir(exist_ok=True, parents=True)
    tools.__try_to_set_owner(tools.whoami(), path)
    return path


def _get_cached_dependencies(config, globals, PYTHON_VERSION):
    # fetch dependencies from odoo lib requirements
    # requirements from odoo framework
    tools = globals["tools"]
    sha = _get_sha(config)

    root_cache_dir = cache_dir(tools)
    tmp_file_name = (
        root_cache_dir / "wodoo" / "reqs" / f"reqs.{sha}.{PYTHON_VERSION}.bin"
    )
    tmp_file_name.parent.mkdir(exist_ok=True, parents=True)
    tools.__try_to_set_owner(tools.whoami(), root_cache_dir)

    _all_submodules_checked_out = all_submodules_checked_out()
    dir_dirty = _dir_dirty(globals)
    if (
        not tmp_file_name.exists()
        or not _all_submodules_checked_out
        or dir_dirty
    ):
        lib_python_dependencies = (
            (config.dirs["odoo_home"] / "requirements.txt").read_text().split("\n")
        )

        # fetch the external python dependencies
        external_dependencies = globals["Modules"].get_all_external_dependencies(
            additional_modules=MINIMAL_MODULES
        )
        if external_dependencies:
            for key in sorted(external_dependencies):
                if not external_dependencies[key]:
                    continue
                click.secho(
                    "\nDetected external dependencies {}: {}".format(
                        key, ", ".join(map(str, external_dependencies[key]))
                    ),
                    fg="green",
                )

        tools = globals["tools"]

        external_dependencies.setdefault("pip", [])
        external_dependencies.setdefault("deb", [])

        requirements_odoo = config.WORKING_DIR / "odoo" / "requirements.txt"
        if requirements_odoo.exists():
            for libpy in requirements_odoo.read_text().split("\n"):
                libpy = libpy.strip()

                if ";" in libpy or tools._extract_python_libname(libpy) not in (
                    tools._extract_python_libname(x)
                    for x in external_dependencies.get("pip", [])
                ):
                    # gevent is special; it has sys_platform set - several lines;
                    external_dependencies["pip"].append(libpy)

        for libpy in lib_python_dependencies:
            if tools._extract_python_libname(libpy) not in (
                tools._extract_python_libname(x)
                for x in external_dependencies.get("pip", [])
            ):
                external_dependencies["pip"].append(libpy)

        arr2 = []
        for libpy in external_dependencies["pip"]:
            # PATCH python renamed dateutils to
            if "dateutil" in libpy and PYTHON_VERSION >= (3, 8, 0):
                if not re.findall("python.dateutil.*", libpy):
                    libpy = libpy.replace("dateutil", "python-dateutil")
            arr2.append(libpy)
        external_dependencies["pip"] = list(sorted(arr2))

        external_dependencies["pip"] = list(
            sorted(
                filter(
                    lambda x: x not in ["ldap"],
                    list(sorted(external_dependencies["pip"])),
                )
            )
        )
        if not _all_submodules_checked_out:
            return external_dependencies

        tmp_file_name.write_text(json.dumps(external_dependencies))

    return json.loads(tmp_file_name.read_text())
