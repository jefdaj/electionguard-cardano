import pytest
from egc import *
import logging

LOG = logging.getLogger(__name__)

@pytest.mark.local
def test_admin_wallet(admin_wallet: Wallet):
    assert isinstance(admin_wallet, Wallet)
    assert isinstance(admin_wallet.sk, SigningKey)
    assert isinstance(admin_wallet.addr, Address)
    assert isinstance(admin_wallet.vk, VerificationKey)
    assert isinstance(admin_wallet.vkh, VerificationKeyHash)

@pytest.mark.local
def test_load_admin_wallet_by_address(admin_wallet: Wallet, keys_dir: Path) -> Wallet:
    (_, w2) = load_wallet_by_address(admin_wallet.addr, keys_dir)
    assert w2 == admin_wallet

@pytest.mark.local
def test_subchannel_wallets(
        guardian1_wallet: Wallet,
        guardian2_wallet: Wallet,
        guardian3_wallet: Wallet,
        device1_wallet: Wallet,
        verifier1_wallet: Wallet,
    ):
        assert isinstance(guardian1_wallet, Wallet)
        assert isinstance(guardian2_wallet, Wallet)
        assert isinstance(guardian3_wallet, Wallet)
        assert isinstance(device1_wallet, Wallet)
        assert isinstance(verifier1_wallet, Wallet)
