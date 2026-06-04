import pytest
import logging

pytest_plugins = [
    "fixtures.admin",
    "fixtures.assets",
    "fixtures.election",
    "fixtures.funder",
    "fixtures.ogmios",
    "fixtures.script",
    "fixtures.wallet",
]

def pytest_configure(config):
    logging.getLogger('websockets').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
