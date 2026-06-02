import pytest
from egc import *

def test_roundrip_utxo_to_dict(oneshot_utxo: UTxO):
    tmp = oneshot_utxo.to_cbor_hex()
    utxo2 = UTxO.from_cbor(bytes.fromhex(tmp))
    assert utxo2 == oneshot_utxo

def test_roundtrip_script_to_dict(script: ElectionScript):
    tmp = script.to_dict()
    script2 = ElectionScript.from_dict(data=tmp)
    assert script == script2
