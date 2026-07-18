import pytest
from egc import *
import logging

LOG = logging.getLogger(__name__)

@pytest.mark.testnet
def test_roundtrip_deployment(dummy_deployment: ElectionDeployment):
    tmp = dummy_deployment.to_dict()
    LOG.debug(f'dummy_deployment dict: {tmp}')
    dd2 = ElectionDeployment.from_dict(tmp)
    assert dd2 == dummy_deployment

@pytest.mark.testnet
def test_roundtrip_electioncontext(dummy_electioncontext: ElectionContext):
    tmp = dummy_electioncontext.to_dict()
    LOG.debug(f'dummy_electioncontext dict: {tmp}')
    dec2 = ElectionContext.from_dict(tmp)
    assert dec2 == dummy_electioncontext

@pytest.mark.testnet
def test_init_tx(init_tx: Transaction):
    # This is mainly for testing that the teardown works.
    # TODO is there a better way to do that explicitly?
    assert isinstance(init_tx, Transaction)

@pytest.mark.testnet
def test_election_config(config: ElectionConfig):
    assert isinstance(config, ElectionConfig)

@pytest.mark.testnet
def test_election_context(election: ElectionContext):
    assert isinstance(election, ElectionContext)
