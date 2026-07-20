import pytest
import logging

# Modules that pytest should mess with by inserting assert introspection stuff.
# Add any helper modules used in the tests here.
pytest.register_assert_rewrite("tests.helpers")

def pytest_configure(config):
    # These are all probably worth looking at again if/when we have mysterious
    # API issues. But the rest of the time they're pretty noisy.
    logging.getLogger('websockets').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.INFO)
    logging.getLogger('ogmios').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('aiphttp').setLevel(logging.WARNING)

pytest_plugins = [

	# stage 1 fixtures
    # TODO separate the actually global ones?
    "tests.fixtures.static_records",
    "tests.fixtures.admin",
    "tests.fixtures.funder",
    "tests.fixtures.subchannels_offline",
    "tests.fixtures.wallet",

    # stage 2 fixtures
    "tests.s2_minimal_network.fixtures.admin_minimal",
    "tests.s2_minimal_network.fixtures.assets",
    "tests.s2_minimal_network.fixtures.election",
    "tests.s2_minimal_network.fixtures.network",
    "tests.s2_minimal_network.fixtures.script",
    "tests.s2_minimal_network.fixtures.subchannels_online",

    # TODO stage 3 fixtures

]
