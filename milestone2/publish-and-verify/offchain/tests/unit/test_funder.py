import logging
import pytest

LOG = logging.getLogger(__name__)

from pycardano import *

def test_funder_sk(funder_sk: SigningKey):
    assert isinstance(funder_sk, SigningKey)

def test_funder_addr(funder_addr: Address):
    assert isinstance(funder_addr, Address)

def test_funder_vkh(funder_vkh: VerificationKeyHash):
    assert isinstance(funder_vkh, VerificationKeyHash)
