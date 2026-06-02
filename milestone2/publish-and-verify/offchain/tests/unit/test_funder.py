import pytest
from egc import *
import logging

LOG = logging.getLogger(__name__)

def test_pick_oneshot_utxo(oneshot_utxo: UTxO):
    assert isinstance(oneshot_utxo, UTxO)

def test_init_funder(funder: Funder):
    assert isinstance(funder, Funder)
    assert isinstance(funder.publisher, ElectionPublisher)

def test_parameterize_script(script: ElectionScript):
    assert isinstance(script, ElectionScript)

def test_build_init_tx(init_tx: TransactionBuilder):
    assert isinstance(init_tx, TransactionBuilder)
