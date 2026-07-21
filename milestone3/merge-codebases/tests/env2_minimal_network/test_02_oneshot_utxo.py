import pytest
from egc import *
import logging

LOG = logging.getLogger(__name__)

def test_pick_oneshot_utxo(oneshot_utxo: UTxO):
    assert isinstance(oneshot_utxo, UTxO)

    # TODO is there a good way to test these before init_election?
    # assert funder.election is None
    # assert funder.subscriber is None

    # TODO any other init tests?

# def test_init_tx_builder(init_tx_builder: TransactionBuilder):
#     assert isinstance(init_tx_builder, TransactionBuilder)
