import re
import base64
import click
import yaml
import inspect
import os
from pathlib import Path
import shutil

current_dir = Path(
    os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
)


def after_compose(config, settings, yml, globals):
    dirs = config.dirs

    # make dummy history file for pgcli
    file = dirs["run"] / "pgcli_history"
    if not file.exists():
        file.write_text("")
    if file.owner() != "root" or file.group() != "root":
        globals['tools'].__try_to_set_owner(0, file)
