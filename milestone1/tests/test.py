#!/usr/bin/env python3

import subprocess
import sys

if __name__ == '__main__':
    args = ['pytest', 'election.py', '-vv'] + sys.argv[1:]
    subprocess.check_call(args)
