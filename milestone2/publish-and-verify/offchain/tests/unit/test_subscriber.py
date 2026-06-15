import pytest
from helpers import per_election_fixture
from egc import *
import logging
import time

LOG = logging.getLogger(__name__)

# This is a little weird because there are also 2 other subscribers implicit in
# starting an election: funder and admin. I think it's still worth explicitly
# testing a 3rd. Most of the more detailed tests do have to be interleaved with
# their election steps in other test modules though.

@per_election_fixture
def sub_cfg(election: ElectionContext):
    return SubscriberConfig.from_election(election)

@per_election_fixture
def subscriber(sub_cfg: SubscriberConfig):
    sub = ElectionSubscriber(sub_cfg)
    sub.start()
    time.sleep(1) # TODO remove?
    yield sub
    sub.stop()

@pytest.mark.testnet
def test_init_subscriber(
        election: ElectionContext,
        subscriber: ElectionSubscriber,
    ):
    assert isinstance(subscriber, ElectionSubscriber)
    # assert subscriber.channel_ids() == [ADMIN_CHANNEL_ID]
    # admin_history = subscriber.channel_history(ADMIN_CHANNEL_ID)
    # assert len(admin_history) == 1
    # assert 0 in admin_history # TODO is it a dict tho?
