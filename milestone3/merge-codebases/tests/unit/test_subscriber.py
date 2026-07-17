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

@pytest.mark.testnet
def test_rollback(
        election: ElectionContext,
        subscriber: ElectionSubscriber,
    ):

    # This just simulates a single block rollback in a low effort way;
    # for production testing we probably need a local testnet?
    # TODO do a couple slightly better versions with multiple events?

    # Wait until there are at least 2 blocks to test the more complicated rollback path.
    while len(subscriber._checkpoints) < 2:
        time.sleep(5)

    before = subscriber.all_history()

    # This triggers a rollback, which includes re-fetching matches,
    # and then sends the new matches through the normal process.
    subscriber._handle_matches( subscriber._handle_rollback() )

    time.sleep(5) # TODO how long is actually required?
    after = subscriber.all_history()

    # There presumably wasn't a real rollback during this period,
    # so the new history should come out exactly the same.
    assert before == after

@pytest.mark.testnet
def test_admin_address(init_tx: Transaction, admin: AdminNode):
    actual_addr = admin.publisher.wallet.addr
    found_addr: Optional[Address] = admin.subscriber.admin_address()
    assert isinstance(found_addr, Address)
    assert found_addr == actual_addr
