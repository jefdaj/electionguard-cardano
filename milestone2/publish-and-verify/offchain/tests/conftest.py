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
    "fixtures.data",
    "fixtures.subchannels",
]

def pytest_configure(config):
    # These are all probably worth looking at again if/when we have mysterious
    # API issues. But the rest of the time they're pretty noisy.
    logging.getLogger('websockets').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.DEBUG)
    logging.getLogger('ogmios').setLevel(logging.WARNING)
