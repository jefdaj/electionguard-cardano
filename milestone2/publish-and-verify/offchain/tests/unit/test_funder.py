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

def test_init_funder_node(funder_node: FunderNode):
    assert isinstance(funder_node, FunderNode)
    assert isinstance(funder_node.publisher, ElectionPublisher)

    # TODO is there a good way to test these before init_election?
    # assert funder_node.election is None
    # assert funder_node.subscriber is None

    # TODO any other init tests?

def test_init_txb(init_txb: TransactionBuilder):
    assert isinstance(init_txb, TransactionBuilder)
