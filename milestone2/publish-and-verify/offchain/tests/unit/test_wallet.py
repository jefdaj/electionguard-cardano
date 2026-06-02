import pytest
from egc import *

def test_load_funder_keys(funder_keys: KeyPair):
    assert isinstance(funder_keys, KeyPair)
    assert isinstance(funder_keys.sk, SigningKey)
    assert isinstance(funder_keys.addr, Address)
    assert isinstance(funder_keys.vkh, VerificationKeyHash)

def test_create_admin_keys(admin_keys: KeyPair):
    assert isinstance(admin_keys, KeyPair)
    assert isinstance(admin_keys.sk, SigningKey)
    assert isinstance(admin_keys.addr, Address)
    assert isinstance(admin_keys.vkh, VerificationKeyHash)
