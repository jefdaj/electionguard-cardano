import pytest
from test_utils import local_test
from egc import *

@local_test
def test_roundrip_utxo(oneshot_utxo: UTxO):
    tmp = oneshot_utxo.to_cbor_hex()
    utxo2 = UTxO.from_cbor(bytes.fromhex(tmp))
    assert utxo2 == oneshot_utxo

@local_test
def test_parameterize_script(script: ElectionScript):
    assert isinstance(script, ElectionScript)

@local_test
def test_roundtrip_script(script: ElectionScript):
    tmp = script.to_dict()
    script2 = ElectionScript.from_dict(data=tmp)
    assert script == script2
