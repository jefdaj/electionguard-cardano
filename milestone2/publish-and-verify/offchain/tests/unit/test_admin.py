import pytest
from egc import *
import logging

LOG = logging.getLogger(__name__)

def test_admin_wallet(admin_wallet: Wallet):
    assert isinstance(admin_wallet, Wallet)
    assert isinstance(admin_wallet.sk, SigningKey)
    assert isinstance(admin_wallet.addr, Address)
    assert isinstance(admin_wallet.vk, VerificationKey)
    assert isinstance(admin_wallet.vkh, VerificationKeyHash)

def test_load_admin_wallet_by_address(admin_wallet: Wallet, keys_dir: Path) -> Wallet:
    kp2 = load_wallet_by_address(admin_wallet.addr, keys_dir)
    assert kp2 == admin_wallet

def test_init_admin(admin: AdminNode):
    assert isinstance(admin, AdminNode)
    assert isinstance(admin.election, ElectionContext)
    assert isinstance(admin.publisher, ElectionPublisher)
    assert isinstance(admin.subscriber, ElectionSubscriber)
