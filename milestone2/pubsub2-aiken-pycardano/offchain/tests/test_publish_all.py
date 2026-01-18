import pytest
from pubsub import *
from .conftest import *

# TODO shorten? currently takes about 7 min
@pytest.fixture(scope='module')
def pub_all_open(pub0_open: Publisher, cids_all: CIDs) -> Publisher:
    pub = pub0_open
    for cids in chunks(cids_all, 10):
        tx = pub.publish_cids(cids)
        pub.wait_for_confirmation(tx)
    return pub

@pytest.fixture(scope='module')
def pub_all_closed(pub_all_open: Publisher) -> Publisher:
    pub = pub_all_open
    close_tx = pub.close_channel()
    pub.wait_for_confirmation(close_tx)
    return pub
