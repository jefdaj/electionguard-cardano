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
    # logging.getLogger('egc.core.subscriber').setLevel(logging.INFO)
    logging.getLogger('egc.core.node').setLevel(logging.DEBUG)
    logging.getLogger('egc.core.publisher').setLevel(logging.DEBUG)
    logging.getLogger('egc.core.subscriber').setLevel(logging.INFO)
    logging.getLogger('egc.nodes.admin').setLevel(logging.DEBUG)
    logging.getLogger('egc.nodes.ipfs').setLevel(logging.DEBUG)


pytest_plugins = [

    # stage 1 fixtures
    # TODO separate the actually global ones?
    "tests.env1_no_containers.fixtures.tmp_root",
    "tests.env1_no_containers.fixtures.admin",
    "tests.env1_no_containers.fixtures.funder",
    "tests.env1_no_containers.fixtures.subchannels",
    "tests.env1_no_containers.fixtures.wallet",

    # stage 2 fixtures
    "tests.env2_minimal_network.fixtures.tmp_root",
    "tests.env2_minimal_network.fixtures.funder",
    "tests.env2_minimal_network.fixtures.admin",
    "tests.env2_minimal_network.fixtures.assets",
    "tests.env2_minimal_network.fixtures.election",
    "tests.env2_minimal_network.fixtures.network",
    "tests.env2_minimal_network.fixtures.script",
    "tests.env2_minimal_network.fixtures.static_records",
    "tests.env2_minimal_network.fixtures.subchannels",

    # stage 3 fixtures
    "tests.env3_generated_networks.fixtures.random_seed",
    "tests.env3_generated_networks.fixtures.tmp_root",
    "tests.env3_generated_networks.fixtures.arion_dir",
    # "tests.env3_generated_networks.fixtures.arion_network",

]
