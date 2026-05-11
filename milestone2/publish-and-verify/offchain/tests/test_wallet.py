import pytest
from election.wallet import *
from .conftest import *
from pprint import pprint

def test_load_wallet_addr(addr: Address):
    assert isinstance(addr, Address)

def test_load_wallet_sk(sk: SigningKey):
    assert isinstance(sk, SigningKey)

def test_load_wallet_vkh(vkh: VerificationKeyHash):
    assert isinstance(vkh, VerificationKeyHash)
