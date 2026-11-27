import pytest

import importlib
import pkgutil
import egc
import subprocess
import sys

from .lib import run

import logging
LOG = logging.getLogger(__name__)


def test_all_modules_import():
    failures = []

    for module in pkgutil.walk_packages(
        egc.__path__,
        prefix=egc.__name__ + ".",
    ):
        try:
            importlib.import_module(module.name)
            LOG.debug(f'import {module.name}')
        except Exception as exc:
            failures.append(f"{module.name}: {exc!r}")

    assert not failures, "Import failures:\n" + "\n".join(failures)


# TODO also test the server is healthy after starting the container


def test_egc_binary_runs():
    result = subprocess.run(
        ["egc"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_compileall():
    run(sys.executable, "-m", "compileall", "-q", "src")
    run(sys.executable, "-m", "compileall", "-q", "tests")
