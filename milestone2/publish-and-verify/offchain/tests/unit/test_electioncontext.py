import pytest
from egc import *

def test_roundtrip_deployment(dummy_deployment: ElectionDeployment):
    tmp = dummy_deployment.to_dict()
    dd2 = ElectionDeployment.from_dict(tmp)
    assert dd2 == dummy_deployment

def test_roundtrip_electioncontext(dummy_electioncontext: ElectionContext):
    tmp = dummy_electioncontext.to_dict()
    dec2 = ElectionContext.from_dict(tmp)
    assert dec2 == dummy_electioncontext

# def test_init_script(script: ElectionScript):
#     assert isinstance(script, ElectionScript)
#     assert isinstance(script.mint_script, bytes)
#     assert isinstance(script.spend_script, bytes)
#     assert isinstance(script.policy_id, ScriptHash)
#     assert isinstance(script.address, Address)
