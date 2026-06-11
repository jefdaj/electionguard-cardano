import pytest
from test_utils import local_test
from egc import *
import logging

LOG = logging.getLogger(__name__)

@local_test
def test_funder_wallet(funder_wallet: Wallet):
    assert isinstance(funder_wallet, Wallet)
    assert isinstance(funder_wallet.sk, SigningKey)
    assert isinstance(funder_wallet.addr, Address)
    assert isinstance(funder_wallet.vkh, VerificationKeyHash)

@local_test
def test_pick_oneshot_utxo(oneshot_utxo: UTxO):
    assert isinstance(oneshot_utxo, UTxO)

@local_test
def test_init_funder(funder: FunderNode):
    assert isinstance(funder, FunderNode)
    assert isinstance(funder.publisher, ElectionPublisher)

    # TODO is there a good way to test these before init_election?
    # assert funder.election is None
    # assert funder.subscriber is None

    # TODO any other init tests?

@local_test
def test_init_tx_builder(init_tx_builder: TransactionBuilder):
    assert isinstance(init_tx_builder, TransactionBuilder)
