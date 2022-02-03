import sys
import re
import base64
import click
import yaml
import inspect
import os
import subprocess
from pathlib import Path
dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))


def after_compose(config, settings, yml, globals):
    # store also in clear text the requirements
    from wodoo.tools import get_services
    from pathlib import Path
    yml['services']['robot']['build']['args']['OWNER_UID'] = config.owner_uid