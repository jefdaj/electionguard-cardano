import pytest
from test_utils import local_test, testnet_test
from egc import *
import logging

LOG = logging.getLogger(__name__)

@local_test
def test_roundtrip_deployment(dummy_deployment: ElectionDeployment):
    tmp = dummy_deployment.to_dict()
    LOG.debug(f'dummy_deployment dict: {tmp}')
    dd2 = ElectionDeployment.from_dict(tmp)
    assert dd2 == dummy_deployment

@local_test
def test_roundtrip_electioncontext(dummy_electioncontext: ElectionContext):
    tmp = dummy_electioncontext.to_dict()
    LOG.debug(f'dummy_electioncontext dict: {tmp}')
    dec2 = ElectionContext.from_dict(tmp)
    assert dec2 == dummy_electioncontext

# TODO rename something less ambiguous?
@testnet_test
def test_election(election: ElectionContext):
    assert isinstance(election, ElectionContext)
