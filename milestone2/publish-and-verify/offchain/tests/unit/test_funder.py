import pytest
from egc import *
import logging

LOG = logging.getLogger(__name__)

def test_funder_keys(funder_keys: KeyPair):
    assert isinstance(funder_keys, KeyPair)
    assert isinstance(funder_keys.sk, SigningKey)
    assert isinstance(funder_keys.addr, Address)
    assert isinstance(funder_keys.vkh, VerificationKeyHash)

def test_pick_oneshot_utxo(oneshot_utxo: UTxO):
    assert isinstance(oneshot_utxo, UTxO)

def test_init_funder(funder: Funder):
    assert isinstance(funder, Funder)
    assert isinstance(funder.publisher, ElectionPublisher)

def test_init_txb(init_txb: TransactionBuilder):
    assert isinstance(init_txb, TransactionBuilder)

# def test_init_tx(funder: Funder, init_txb: TransactionBuilder):
#     raise NotImplementedError
