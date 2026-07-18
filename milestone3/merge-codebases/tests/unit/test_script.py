import pytest
from egc import *

@pytest.mark.local
def test_roundrip_oneshot_utxo(oneshot_utxo: UTxO):
    tmp = oneshot_utxo.to_cbor_hex()
    utxo2 = UTxO.from_cbor(bytes.fromhex(tmp))
    assert utxo2 == oneshot_utxo

@pytest.mark.local
def test_parameterize_script(script: ElectionScript):
    assert isinstance(script, ElectionScript)

@pytest.mark.testnet
def test_roundtrip_script(script: ElectionScript):
    tmp = script.to_dict()
    script2 = ElectionScript.from_dict(data=tmp)
    assert script == script2
