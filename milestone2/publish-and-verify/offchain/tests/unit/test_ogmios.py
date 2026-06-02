import pytest
from egc import *

def test_ogmios_up(ogmios: OgmiosV6ChainContext):
    assert ogmios.last_block_slot > 101181854

def test_query_network_tip(ogmios: OgmiosV6ChainContext):
    tip = query_network_tip_sync()
    assert isinstance(tip, dict)
    assert isinstance(tip['slot'], int)
    assert isinstance(tip['block_hash'], str)
