import pytest
from egc import *

def test_funder_sk(funder_sk: SigningKey):
    assert isinstance(funder_sk, SigningKey)

def test_funder_addr(funder_addr: Address):
    assert isinstance(funder_addr, Address)

def test_funder_vkh(funder_vkh: VerificationKeyHash):
    assert isinstance(funder_vkh, VerificationKeyHash)

def test_pick_oneshot_utxo(oneshot_utxo: UTxO):
    assert isinstance(oneshot_utxo, UTxO)
