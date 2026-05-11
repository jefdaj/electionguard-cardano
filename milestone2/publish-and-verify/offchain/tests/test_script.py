import pytest
from .conftest import *
from election.plutus.script import *

def test_pick_oneshot_utxo(oneshot_utxo: UTxO):
    assert isinstance(oneshot_utxo, UTxO)

def test_init_script(oneshot_utxo: UTxO):
    script = ElectionScript(oneshot_utxo)
    assert isinstance(script, ElectionScript)
    assert isinstance(script.mint_script, bytes)
    assert isinstance(script.spend_script, bytes)
    assert isinstance(script.policy_id, ScriptHash)
    assert isinstance(script.address, Address)
