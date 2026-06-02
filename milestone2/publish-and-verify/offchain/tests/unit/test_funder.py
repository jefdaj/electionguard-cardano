import pytest
from egc import *

def test_pick_oneshot_utxo(oneshot_utxo: UTxO):
    assert isinstance(oneshot_utxo, UTxO)

def test_init_funder(funder: Funder):
    assert isinstance(funder, Funder)
    assert isinstance(funder.publisher, ElectionPublisher)
