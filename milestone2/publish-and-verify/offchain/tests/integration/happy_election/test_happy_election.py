# Test order roughly matches onchain/tests/integration/happy_election.ak

import pytest
from pycardano import *
from egc import *
from test_utils import per_election_fixture, assert_subscribers_in_sync
from static_records import STATIC_PHASES, STATIC_TRANSACTIONS
import logging
import time

LOG = logging.getLogger(__name__)

SUBCHANNEL_IDS = STATIC_TRANSACTIONS['admin'][2][0].channels
[G1, G2, G3, D1, V1] = SUBCHANNEL_IDS


### subchannel wallets ###

@per_election_fixture
def guardian1_wallet(keys_dir: Path) -> Wallet:
    w = Wallet.load_or_create(name='guardian1', keys_dir=keys_dir, verbose=False)
    LOG.debug(f'guardian1_wallet: {w}')
    return w

@per_election_fixture
def guardian2_wallet(keys_dir: Path) -> Wallet:
    w = Wallet.load_or_create(name='guardian2', keys_dir=keys_dir, verbose=False)
    LOG.debug(f'guardian2_wallet: {w}')
    return w

@per_election_fixture
def guardian3_wallet(keys_dir: Path) -> Wallet:
    w = Wallet.load_or_create(name='guardian3', keys_dir=keys_dir, verbose=False)
    LOG.debug(f'guardian3_wallet: {w}')
    return w

@per_election_fixture
def device1_wallet(keys_dir: Path) -> Wallet:
    w = Wallet.load_or_create(name='device1', keys_dir=keys_dir, verbose=False)
    LOG.debug(f'device1_wallet: {w}')
    return w

@per_election_fixture
def verifier1_wallet(keys_dir: Path) -> Wallet:
    w = Wallet.load_or_create(name='verifier1', keys_dir=keys_dir, verbose=False)
    LOG.debug(f'verifier1_wallet: {w}')
    return w

def test_subchannel_wallets(
        guardian1_wallet: Wallet,
        guardian2_wallet: Wallet,
        guardian3_wallet: Wallet,
        device1_wallet: Wallet,
        verifier1_wallet: Wallet,
    ):
        assert isinstance(guardian1_wallet, Wallet)
        assert isinstance(guardian2_wallet, Wallet)
        assert isinstance(guardian3_wallet, Wallet)
        assert isinstance(device1_wallet, Wallet)
        assert isinstance(verifier1_wallet, Wallet)


### admin_tx0 ###

@per_election_fixture
def admin_s0(admin_vkh: VerificationKeyHash) -> ChannelState:
    return AdminChannel(state=AdminChannelState(
        admin       = admin_vkh.payload,
        subchannels = [],
        new_records = [],
        phase       = ElectionConfigPhase(ConfigAnnouncePhase()),
        seq         = 0,
    ))

@per_election_fixture
def admin_tx0(init_tx: Transaction) -> Transaction:
    # admin_tx0 is just the init_tx renamed for clarity.
    time.sleep(5) # TODO remove?
    return init_tx

def test_admin_tx0(
        admin: AdminNode,
        admin_s0: ChannelState,
        admin_tx0: Transaction,
    ):
    LOG.debug(f'admin_tx0: {admin_tx0}')
    assert isinstance(admin_tx0, Transaction)

    # admin state should match admin_s0
    # we could use funder.subscriber here; they should match
    actual_state = admin.subscriber.states[ADMIN_CHANNEL_ID][1]
    assert actual_state == admin_s0

# ... in fact, all nodes should agree on the current state
def test_admin_tx0_sub(
        funder: FunderNode,
        admin: AdminNode,
        admin_tx0: Transaction,
    ):
    assert_subscribers_in_sync([funder, admin])


### admin_tx1 ###

@per_election_fixture
def admin_s1(admin_vkh: VerificationKeyHash) -> ChannelState:
    return AdminChannel(state=AdminChannelState(
        admin       = admin_vkh.payload,
        subchannels = [],
        new_records = STATIC_TRANSACTIONS['admin'][1][1],
        phase       = STATIC_PHASES[1],
        seq         = 1,
    ))

@per_election_fixture
def admin_tx1(
        admin: AdminNode,
        admin_tx0: Transaction,
    ) -> Transaction:
    tx = admin.post_public_records(
        new_records = STATIC_TRANSACTIONS['admin'][1][1],
        new_phase   = STATIC_PHASES[1],
    )
    LOG.debug(f'admin_tx1: {tx}')
    admin.publisher.wait_for_confirmation(tx)
    time.sleep(5) # TODO remove?
    return tx

def test_admin_tx1(
        admin: AdminNode,
        admin_s1: ChannelState,
        admin_tx1: Transaction,
    ):
    assert isinstance(admin_tx1, Transaction)
    actual_state = admin.subscriber.states[ADMIN_CHANNEL_ID][1]
    assert actual_state == admin_s1

def test_admin_tx1_sub(
        funder: FunderNode,
        admin: AdminNode,
        admin_tx1: Transaction,
    ):
    assert_subscribers_in_sync([funder, admin])


### admin_tx2 ###

@per_election_fixture
def subchannel_wallets(
        guardian1_wallet: Wallet,
        guardian2_wallet: Wallet,
        guardian3_wallet: Wallet,
        device1_wallet: Wallet,
        verifier1_wallet: Wallet,
    ) -> dict[ChannelId, Wallet]:
    wallets = [
        guardian1_wallet,
        guardian2_wallet,
        guardian3_wallet,
        device1_wallet,
        verifier1_wallet,
    ]
    return {k:v for (k,v) in zip(SUBCHANNEL_IDS, wallets)} # TODO sort?

@per_election_fixture
def subchannel_onboarding_info(
        subchannel_wallets: dict[ChannelId, Wallet]
    ) -> dict[ChannelId, VerificationKeyHash]:
    return {i:w.vkh for (i,w) in subchannel_wallets.items()} # TODO sort?

@per_election_fixture
def admin_s2(admin_vkh: VerificationKeyHash) -> ChannelState:
    return AdminChannel(state=AdminChannelState(
        admin       = admin_vkh.payload,
        subchannels = SUBCHANNEL_IDS,
        new_records = [],
        phase       = STATIC_PHASES[2],
        seq         = 2,
    ))

# all the subchannels also have this one as their state0
# aliases for clarity:
guardian1_s0 = admin_s2
guardian_s0  = admin_s2
guardian3_s0 = admin_s2
device1_s0   = admin_s2
verifier1_s0 = admin_s2

@per_election_fixture
def admin_tx2(
        admin_tx1: Transaction,
        admin: AdminNode,
        subchannel_onboarding_info: dict[ChannelId, VerificationKeyHash],
    ) -> Transaction:
    tx = admin.add_subchannels(
        subchannels = subchannel_onboarding_info,
        subchannel_ada = 10,
        done_onboarding = True,
    )
    LOG.debug(f'admin_tx2: {tx}')
    admin.publisher.wait_for_confirmation(tx)
    time.sleep(5) # TODO remove?
    return tx

def sub_s0(sub_id: ChannelId, sub_wallet: Wallet) -> ChannelState:
    return SubChannel(state=SubChannelState(
        channel_id  = sub_id,
        publisher   = sub_wallet.vkh.payload,
        new_records = [],
        seq         = 0,
    ))

def test_admin_tx2(
        admin: AdminNode,
        subchannel_wallets: dict[ChannelId, Wallet],
        admin_s2: ChannelState,
        admin_tx2: Transaction,
    ):
    assert isinstance(admin_tx2, Transaction)

    actual_state = admin.subscriber.states[ADMIN_CHANNEL_ID][1]
    assert actual_state == admin_s2, 'admin unexpected state'

    for (sub_id, sub_wallet) in subchannel_wallets.items():
        actual_state = admin.subscriber.states[sub_id][1]
        assert actual_state == sub_s0(sub_id, sub_wallet), f'{sub_id} unexpected state'

def test_admin_tx2_sub(
        admin_tx2: Transaction,
        funder: FunderNode,
        admin: AdminNode,
    ):
    assert_subscribers_in_sync([funder, admin])
