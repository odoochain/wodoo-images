#!/root/.local/pipx/venvs/wodoo/bin/python3
from datetime import datetime
import json
import os
import sys
import click
import subprocess
from wodoo.module_tools import Module
from wodoo.odoo_config import customs_dir
from wodoo.odoo_config import current_version
from pathlib import Path
from tools import exec_odoo
from tools import prepare_run
import argparse
parser = argparse.ArgumentParser(description='Unittest.')
parser.add_argument('--log-level')
parser.add_argument('--not-interactive', action="store_true")
parser.add_argument('--remote-debug', action="store_true")
parser.add_argument('--wait-for-remote', action="store_true")
parser.add_argument('--resultsfile')
parser.add_argument('test_file')
parser.set_defaults(log_level='debug')
args = parser.parse_args()

os.environ['TEST_QUEUE_JOB_NO_DELAY'] = '1'

if not args.not_interactive:
    os.environ["PYTHONBREAKPOINT"] = "pudb.set_trace"
else:
    os.environ["PYTHONBREAKPOINT"] = "0"

prepare_run()

runs = []

for filepath in args.test_file.split(','):
    started = datetime.now()
    cmd = [
        '--stop-after-init',
        f'--log-level={args.log_level}',
    ]
    filepath = Path(filepath.strip())
    if not str(filepath).startswith("/"):
        filepath = Path(os.environ['CUSTOMS_DIR']) / filepath
    if not filepath.exists():
        click.secho(f"File not found: {filepath}", fg='red')
        sys.exit(-1)
    os.chdir('/opt/src')
    module = Module(filepath)
    cmd += [
        f'--test-file={filepath.resolve().absolute()}',
    ]
    if current_version() <= 11.0:
        cmd += [
            '--test-report-directory=/tmp',
        ]
    rc = exec_odoo(
        "config_unittest",
        remote_debug='--remote-debug' in sys.argv,
        wait_for_remote='--wait-for-remote' in sys.argv,
        *cmd,
    )
    runs.append({
        'path': str(filepath.relative_to("/opt/src")),
        'duration': (datetime.now() - started).total_seconds(),
        'rc': rc,
    })

if args.resultsfile:
    output = Path('/opt/out_dir') / args.resultsfile
    output.write_text(json.dumps(runs, indent=4))

if any(x['rc'] for x in runs):
    rc = -1

sys.exit(rc)
