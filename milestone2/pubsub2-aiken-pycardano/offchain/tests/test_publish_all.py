import pytest
from pubsub import *
from .conftest import *

# TODO shorten? currently takes about 7 min
@pytest.fixture(scope='module')
def pub_all(pub0_open: Publisher, cids_all: CIDs) -> Publisher:
    pub = pub0_open
    assert pub.channel_state == 'open' # TODO move to a test
    for cids in chunks(cids_all, 10):
        tx = pub.publish_cids(cids)
        pub.wait_for_confirmation(tx)
    return pub
