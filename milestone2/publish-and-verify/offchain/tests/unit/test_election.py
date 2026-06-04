import pytest
from egc import *
import logging

LOG = logging.getLogger(__name__)

def test_roundtrip_deployment(dummy_deployment: ElectionDeployment):
    tmp = dummy_deployment.to_dict()
    LOG.debug(f'dummy_deployment dict: {tmp}')
    dd2 = ElectionDeployment.from_dict(tmp)
    assert dd2 == dummy_deployment

def test_roundtrip_electioncontext(dummy_electioncontext: ElectionContext):
    tmp = dummy_electioncontext.to_dict()
    LOG.debug(f'dummy_electioncontext dict: {tmp}')
    dec2 = ElectionContext.from_dict(tmp)
    assert dec2 == dummy_electioncontext

# TODO rename something less ambiguous?
def test_election(election: ElectionContext):
    assert isinstance(election, ElectionContext)
