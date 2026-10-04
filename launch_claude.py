"""Optional Claude Code launcher; modifies only the child's environment."""
import shutil
import subprocess
import sys
import os
from config import claude_environment, load_env


def main():
    executable = shutil.which('claude.exe' if os.name == 'nt' else 'claude')
    if not executable:
        raise SystemExit('Native Claude Code is not installed or is not on PATH. Alternatively merge claude-settings.example.json into your user settings.')
    try:
        env = claude_environment(load_env())
    except ValueError as error:
        raise SystemExit(str(error)) from None
    # No shell; do not print the proxy URL because it could contain credentials.
    try:
        return subprocess.call([executable, *sys.argv[1:]], env=env)
    except KeyboardInterrupt:
        return 130


if __name__ == '__main__':
    sys.exit(main())
