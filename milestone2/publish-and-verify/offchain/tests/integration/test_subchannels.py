# Test order roughly matches onchain/tests/integration/happy_subchannel.ak

import pytest
from dataclasses import replace
from pycardano import *
from egc import *
from helpers import per_election_fixture, assert_nodes_sync_in_5min, assert_node_state
import logging
import time

LOG = logging.getLogger(__name__)


## ----------- setup for adding single subchannel -------------

@per_election_fixture
def s0(admin_vkh: VerificationKeyHash) -> ChannelState:
    return AdminChannel(state=AdminChannelState(
        admin       = admin_vkh.payload,
        subchannels = [],
        new_records = [],
        phase       = ElectionConfigPhase(ConfigAnnouncePhase()),
        seq         = 0,
    ))

@per_election_fixture
def tx0(init_tx: Transaction) -> Transaction:
    # tx0 is just the init_tx renamed for clarity.
    return init_tx

# TODO remove?
@pytest.mark.testnet
def test_tx0(
        funder: FunderNode,
        admin: AdminNode,
        s0: ChannelState,
        tx0: Transaction,
    ):
    assert isinstance(tx0, Transaction)
    nodes = [funder, admin]
    assert_nodes_sync_in_5min(nodes)
    assert_node_state(admin, s0)

@per_election_fixture
def s1(
        s0: ChannelState,
        static_transactions,
        static_phases,
    ) -> ChannelState:
    prev = s0.state
    return AdminChannel(state=replace(
        prev,
        new_records = static_transactions['admin'][1][1],
        phase       = static_phases[1],
        seq         = 1,
    ))

@per_election_fixture
def tx1(
        tx0: Transaction,
        admin: AdminNode,
        static_transactions,
        static_phases,
    ) -> Transaction:
    tx = admin.post_public_records(
        new_records = static_transactions['admin'][1][1],
        new_phase   = static_phases[1],
    )
    LOG.debug(f'tx1: {tx}')
    admin.wait_for_confirmation(tx)
    return tx

# TODO remove?
@pytest.mark.testnet
def test_tx1(
        funder: FunderNode,
        admin: AdminNode,
        s1: ChannelState,
        tx1: Transaction,
    ):
    assert isinstance(tx1, Transaction)
    nodes = [funder, admin]
    assert_nodes_sync_in_5min(nodes)
    assert_node_state(admin, s1)


## -------- tx2: add single subchannel --------

@per_election_fixture
def onboarding_info(
        guardian1: GuardianNode,
    ) -> dict[ChannelId, VerificationKeyHash]:
    info = {
        guardian1.channel_id() : guardian1.publisher.wallet.vkh
    }
    return info

@per_election_fixture
def all_nodes(
        funder: FunderNode,
        admin: AdminNode,
        guardian1: GuardianNode,
    ) -> list[ElectionNode]:
        return [funder, admin, guardian1]

@per_election_fixture
def s2(
        s1: ChannelState,
        onboarding_info: dict[ChannelId, VerificationKeyHash],
        static_phases,
    ) -> ChannelState:
    prev = s1.state
    return AdminChannel(state=replace(
        prev,
        subchannels = [k for k in onboarding_info.keys()],
        new_records = [],
        phase       = static_phases[2],
        seq         = 2, # does matter now
    ))

@per_election_fixture
def tx2(
        tx1: Transaction,
        admin: AdminNode,
        onboarding_info: dict[ChannelId, VerificationKeyHash],
    ) -> Transaction:
    ch_strs = [channel_id_to_string(k) for k in onboarding_info.keys()]
    LOG.info(f'admin got onboarding info from {', '.join(ch_strs)}')
    tx = admin.add_subchannels(
        subchannels = onboarding_info,
        subchannel_ada = 10,
        done_onboarding = True, # TODO remove?
    )
    LOG.debug(f'tx2: {tx}')
    admin.wait_for_confirmation(tx)
    return tx

@pytest.mark.testnet
def test_add_subchannel(
        tx2: Transaction,
        admin: AdminNode,
        all_nodes: list[ElectionNode],
        s2: ChannelState,
    ):
    assert isinstance(tx2, Transaction)
    assert_nodes_sync_in_5min(all_nodes)
    assert_node_state(admin, s2)


## ----------- tx3: rm single subchannel -----------

@per_election_fixture
def s3(
        s2: ChannelState,
    ) -> ChannelState:
    prev = s2.state
    return AdminChannel(state=replace(
        prev,
        subchannels = [],
        new_records = [],
        seq         = 3,
    ))

@per_election_fixture
def tx3(
        tx2: Transaction,
        admin: AdminNode,
        onboarding_info: dict[ChannelId, VerificationKeyHash],
    ) -> Transaction:
    sub_ids = list(onboarding_info.keys())
    ch_strs = [channel_id_to_string(k) for k in sub_ids]
    tx = admin.rm_subchannels(subchannels = sub_ids)
    LOG.debug(f'tx3: {tx}')
    admin.wait_for_confirmation(tx)
    return tx

@pytest.mark.testnet
def test_rm_subchannel(
        admin: AdminNode,
        all_nodes: list[ElectionNode],
        s3: ChannelState,
        tx3: Transaction,
    ):
    assert isinstance(tx3, Transaction)
    assert_nodes_sync_in_5min(all_nodes)
    assert_node_state(admin, s3)
