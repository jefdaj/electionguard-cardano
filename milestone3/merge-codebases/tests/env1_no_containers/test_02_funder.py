import pytest
from egc import *
import logging

LOG = logging.getLogger(__name__)

def test_funder_wallet(funder_wallet: Wallet):
    assert isinstance(funder_wallet, Wallet)
    assert isinstance(funder_wallet.sk, SigningKey)
    assert isinstance(funder_wallet.addr, Address)
    assert isinstance(funder_wallet.vkh, VerificationKeyHash)

def test_init_funder(env1_funder: FunderNode):
    assert isinstance(env1_funder, FunderNode)
    assert isinstance(env1_funder.publisher, ElectionPublisher)
    assert env1_funder.current_phase() == EgcPhase.NOT_INDEXED
