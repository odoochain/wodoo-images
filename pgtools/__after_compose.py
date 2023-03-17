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
    return
