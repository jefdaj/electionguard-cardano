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
    logging.getLogger('aiohttp').setLevel(logging.WARNING)

    # Same with some of our code.
    logging.getLogger('egc.core.subscriber').setLevel(logging.INFO)


pytest_plugins = [

    # stage 1 fixtures
    # TODO separate the actually global ones?
    "tests.s1_offline.fixtures.admin",
    "tests.s1_offline.fixtures.funder",
    "tests.s1_offline.fixtures.subchannels",
    "tests.s1_offline.fixtures.wallet",

    # stage 2 fixtures
    "tests.s2_minimal_network.fixtures.admin",
    "tests.s2_minimal_network.fixtures.assets",
    "tests.s2_minimal_network.fixtures.election",
    "tests.s2_minimal_network.fixtures.network",
    "tests.s2_minimal_network.fixtures.script",
    "tests.s2_minimal_network.fixtures.static_records",
    "tests.s2_minimal_network.fixtures.subchannels",

    # TODO stage 3 fixtures

]
