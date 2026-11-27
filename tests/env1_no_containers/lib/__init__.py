import sys
import subprocess

def run(*args):
    result = subprocess.run(args, text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
