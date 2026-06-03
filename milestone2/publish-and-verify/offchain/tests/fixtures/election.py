import pytest
from datetime import datetime
from pycardano import *
from egc import *
import logging

LOG = logging.getLogger(__name__)

# TODO package (election, scenario) scope Election object, which:
#      1. is a thin wrapper around helper fns from the init_and_burn scenario
#      2. yields the election, then checks if it finished and burns test tokens if needed

# Mainly for testing serialization
@pytest.fixture(scope='package')
def dummy_deployment(
        ogmios: OgmiosV6ChainContext,
        funder_keys: KeyPair
    ) -> ElectionDeployment:
    tip = query_network_tip_sync()
    dd = ElectionDeployment(
        network               = Network.TESTNET,
        funder_address        = funder_keys.addr,
        deployment_date       = datetime.now(),
        index_from_slot       = tip['slot'],
        index_from_block_hash = tip['block_hash'],
    )
    LOG.debug(f'dummy_deployment: {dd}')
    return dd

@pytest.fixture(scope='package')
def dummy_electioncontext(
        script: ElectionScript,
        dummy_deployment: ElectionDeployment,
    ) -> ElectionContext:
    dec = ElectionContext(script=script, deployment=dummy_deployment)
    LOG.debug(f'dummy_electioncontext: {dec}')
    return dec
 
