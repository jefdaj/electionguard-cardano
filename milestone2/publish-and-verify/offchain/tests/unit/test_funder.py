import pytest
from egc import *

def test_funder_sk(funder_keys: KeyPair):
    assert isinstance(funder_keys.sk, SigningKey)

def test_funder_addr(funder_keys: KeyPair):
    assert isinstance(funder_keys.addr, Address)

def test_funder_vkh(funder_keys: KeyPair):
    assert isinstance(funder_keys.vkh, VerificationKeyHash)

def test_pick_oneshot_utxo(oneshot_utxo: UTxO):
    assert isinstance(oneshot_utxo, UTxO)
