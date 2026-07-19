import pytest
import logging

# TODO plugins need to be at the top level, but all other features are nestable?
pytest_plugins = [
    "1_offline.fixtures.data",
    "2_minimal_network.fixtures.admin",
    "2_minimal_network.fixtures.assets",
    "2_minimal_network.fixtures.election",
    "2_minimal_network.fixtures.funder",
    "2_minimal_network.fixtures.ogmios",
    "2_minimal_network.fixtures.script",
    "2_minimal_network.fixtures.wallet",
    "2_minimal_network.fixtures.subchannels",
]

# Tell pytest to print diffs on assertions
pytest.register_assert_rewrite("helpers") # TODO tests.helpers?

def pytest_configure(config):
    # These are all probably worth looking at again if/when we have mysterious
    # API issues. But the rest of the time they're pretty noisy.
    logging.getLogger('websockets').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.INFO)
    logging.getLogger('ogmios').setLevel(logging.WARNING)

    # TODO dial down the subscriber too, either here or at the source
