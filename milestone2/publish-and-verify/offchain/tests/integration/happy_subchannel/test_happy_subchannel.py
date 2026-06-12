# Test order roughly matches onchain/tests/integration/happy_subchannel.ak

import pytest
from dataclasses import replace
from pycardano import *
from egc import *
from test_utils import per_election_fixture, assert_nodes_in_sync
import logging
import time

LOG = logging.getLogger(__name__)


## ----------- nodes -----------

# TODO canonical fixtures for these?

@per_election_fixture
def guardian1_wallet(keys_dir: Path) -> Wallet:
    w = Wallet.load_or_create(name='guardian1', keys_dir=keys_dir, verbose=False)
    LOG.debug(f'guardian1_wallet: {w}')
    return w

@per_election_fixture
def guardian1(
        election: ElectionContext,
        guardian1_wallet: Wallet
    ) -> GuardianNode:
    node = GuardianNode(
        election   = election,
        wallet     = guardian1_wallet,
        role_index = 1,
    )
    LOG.debug(f'guardian1: {node}')
    try:
        yield node
    finally:
        node.stop()


## ----------- add single subchannel -----------

# @per_election_fixture
# def add_action(subchannel_id: ChannelId) -> ElectionAction:
#     return AddSubChannels(channels=[subchannel_id])

@per_election_fixture
def single_onboarding_info(
        guardian1: GuardianNode,
    ) -> dict[ChannelId, VerificationKeyHash]:
    info = {
        guardian1.channel_id() : guardian1.publisher.wallet.vkh
    }
    return info

@per_election_fixture
def single_nodes(
        admin: AdminNode,
        guardian1: GuardianNode,
    ) -> list[ElectionNode]:
        return [admin, guardian1]

@per_election_fixture
def single_admin_pre_add_state(admin_vkh: VerificationKeyHash) -> ChannelState:
    return AdminChannel(state=AdminChannelState(
        admin       = admin_vkh.payload,
        subchannels = [],
        new_records = [],
        phase       = ElectionConfigPhase(ConfigOnboardingPhase()),
        seq         = 2, # doesn't matter as long as it increments each step
    ))

# TODO ah, can't just start here; have to make tx1 etc first
@per_election_fixture
def single_admin_post_add_state(
        admin_pre_add_state: ChannelState,
        onboarding_info: dict[ChannelId, VerificationKeyHash],
    ) -> ChannelState:
    prev = admin_pre_add_state.state
    return AdminChannel(state=replace(
        prev,
        subchannels = [k for k in onboarding_info.keys()],
        seq = prev.seq + 1,
    ))

@per_election_fixture
def single_add_tx(
        admin: AdminNode,
        admin_pre_add_state: ChannelState,
        onboarding_info: dict[ChannelId, VerificationKeyHash],
    ) -> Transaction:
    ch_strs = [channel_id_to_string(k) for k in onboarding_info.keys()]
    LOG.info(f'admin got onboarding info from {', '.join(ch_strs)}')
    tx = admin.add_subchannels(
        subchannels = onboarding_info,
        subchannel_ada = 10,
        done_onboarding = True, # TODO remove?
    )
    LOG.debug(f'admin_tx2: {tx}')
    admin.wait_for_confirmation(tx)
    return tx

@pytest.mark.testnet
def test_single_add_tx(
        admin: AdminNode,
        single_nodes: list[ElectionNode],
        single_add_tx: Transaction,
        single_admin_post_add_state: ChannelState,
    ):
    assert isinstance(single_add_tx, Transaction)
    actual_state = admin.subscriber.states[ADMIN_CHANNEL_ID][1]
    assert actual_state == single_admin_post_add_state, 'admin unexpected state'
    assert_nodes_in_sync(single_nodes)
