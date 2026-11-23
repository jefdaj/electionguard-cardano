import pytest

import importlib
import pkgutil
import egc

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
