# Test order roughly matches onchain/tests/integration/happy_election.ak

import pytest
from dataclasses import replace
from pycardano import *
from egc import *
from helpers import per_election_fixture, assert_nodes_in_sync, assert_node_state, sub_s0
import logging
import time

LOG = logging.getLogger(__name__)


# STATIC_PHASES = \
# {0: ElectionConfigPhase(phase=ConfigAnnouncePhase()),
#  1: ElectionConfigPhase(phase=ConfigOnboardingPhase()),
#  2: ElectionConfigPhase(phase=ConfigCeremonyPhase()),
#  3: ElectionVotingPhase(),
#  4: ElectionResultsPhase(phase=ResultsTallyPhase()),
#  5: ElectionResultsPhase(phase=ResultsDecryptPhase()),
#  6: ElectionVerifyPhase(),
#  7: ElectionFinalizePhase()}


## =================================
## initial solo admin transactions:
## 0. init election
## 1. announce config
## 2. onboarding (add subchannels)
## =================================


## ----------- admin_tx0 -----------

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
    return init_tx

@pytest.mark.testnet
def test_admin_tx0(
        funder: FunderNode,
        admin: AdminNode,
        admin_s0: ChannelState,
        admin_tx0: Transaction,
    ):
    assert isinstance(admin_tx0, Transaction)
    assert_node_state(admin, admin_s0)
    nodes = [funder, admin]
    assert_nodes_in_sync(nodes)


## ----------- admin_tx1 -----------

@per_election_fixture
def admin_s1(
        admin_s0: ChannelState,
        static_transactions,
    ) -> ChannelState:
    prev = admin_s0.state
    return AdminChannel(state=replace(
        prev,
        new_records = static_transactions['admin'][1][1],
        phase       = ElectionConfigPhase(phase=ConfigOnboardingPhase()),
        seq         = 1,
    ))

@per_election_fixture
def admin_tx1(
        admin: AdminNode,
        admin_tx0: Transaction,
        static_transactions,
    ) -> Transaction:
    tx = admin.post_public_records(
        new_records = static_transactions['admin'][1][1],
        new_phase   = ElectionConfigPhase(phase=ConfigOnboardingPhase()),
    )
    LOG.debug(f'admin_tx1: {tx}')
    admin.wait_for_confirmation(tx)
    return tx

@pytest.mark.testnet
def test_admin_tx1(
        funder: FunderNode,
        admin: AdminNode,
        admin_s1: ChannelState,
        admin_tx1: Transaction,
    ):
    assert isinstance(admin_tx1, Transaction)
    assert_node_state(admin, admin_s1)
    nodes = [funder, admin]
    assert_nodes_in_sync(nodes)


# from here on all the nodes can be started and should stay in sync
@per_election_fixture
def all_nodes(
        funder: FunderNode,
        admin: AdminNode,
        subchannel_nodes: list[ElectionNode],
    ) -> list[ElectionNode]:
    return [funder, admin] + subchannel_nodes

# test_phase* make sure the TXs are submitted in a realistic order,
# and that all the states line up as expected at each checkpoint. It's a
# little confusing because each one is tested right after the phase variable
# has advanced to the next phase. For example this one (phase 0) should be
# tested right after having updated to phase 1.
@pytest.mark.testnet
def test_phase0_announce(
        funder,
        admin, admin_s1, admin_tx1,
    ):
    assert_nodes_in_sync([funder, admin])
    assert_node_state(admin, admin_s1)


## ----------- admin_tx2 -----------

@per_election_fixture
def onboarding_info(
        subchannel_nodes: list[ElectionNode],
    ) -> dict[ChannelId, VerificationKeyHash]:
    info = {
        node.channel_id() : node.publisher.wallet.vkh
        for node in subchannel_nodes
    }
    return info

@per_election_fixture
def admin_s2(
        admin_s1: ChannelState,
        subchannel_ids,
        static_phases,
    ) -> ChannelState:
    prev = admin_s1.state
    return AdminChannel(state=replace(
        prev,
        subchannels = subchannel_ids,
        new_records = [],
        phase       = ElectionConfigPhase(phase=ConfigCeremonyPhase()),
        seq         = 2,
    ))

@per_election_fixture
def admin_tx2(
        admin_tx1: Transaction,
        admin: AdminNode,
        onboarding_info: dict[ChannelId, VerificationKeyHash],
    ) -> Transaction:
    ch_strs = [channel_id_to_string(k) for k in onboarding_info.keys()]
    LOG.info(f'admin got onboarding info from {', '.join(ch_strs)}')
    tx = admin.add_subchannels(
        subchannels = onboarding_info,
        subchannel_ada = 10,
        done_onboarding = True,
    )
    LOG.debug(f'admin_tx2: {tx}')
    admin.wait_for_confirmation(tx)
    return tx

@pytest.mark.testnet
def test_admin_tx2(
        admin: AdminNode,
        subchannel_nodes: list[ElectionNode],
        admin_s2: ChannelState,
        admin_tx2: Transaction,
        all_nodes: list[ElectionNode],
    ):
    assert isinstance(admin_tx2, Transaction)
    assert_nodes_in_sync(all_nodes)
    assert_node_state(admin, admin_s2)
    for sub_node in subchannel_nodes:
        expected_state = sub_s0(sub_node.channel_id(), sub_node.publisher.wallet.vkh)
        assert_node_state(sub_node, expected_state)

@pytest.mark.testnet
def test_phase1_onboarding(
        admin, admin_s2, admin_tx2,
        guardian1, guardian1_s0,
        guardian2, guardian2_s0,
        guardian3, guardian3_s0,
        device1, device1_s0,
        verifier1, verifier1_s0,
        all_nodes: list[ElectionNode],
    ):
    assert_nodes_in_sync(all_nodes)
    assert_node_state(admin, admin_s2)
    assert_node_state(guardian1, guardian1_s0)
    assert_node_state(guardian2, guardian2_s0)
    assert_node_state(guardian3, guardian3_s0)
    assert_node_state(device1, device1_s0)
    assert_node_state(verifier1, verifier1_s0)
    # TODO test that subchannel nodes can find their collateral now?


## =================================
## parallel admin section:
## 3. finalize config
## 4. advance voting -> tally
## 5. results tally
## 6. results decrypt
## 7. verify
## =================================


## ----------- admin_tx3 -----------

@per_election_fixture
def admin_s3(
        admin_s2: ChannelState,
        static_transactions,
        static_phases,
    ) -> ChannelState:
    prev = admin_s2.state
    return AdminChannel(state=replace(
        prev,
        new_records = static_transactions['admin'][3][1],
        phase       = static_phases[3],
        seq         = 3,
    ))

@per_election_fixture
def admin_tx3(
        admin: AdminNode,
        admin_tx2: Transaction,
        static_transactions,
        static_phases,
    ) -> Transaction:
    tx = admin.post_public_records(
        new_records = static_transactions['admin'][3][1],
        new_phase   = static_phases[3],
    )
    LOG.debug(f'admin_tx3: {tx}')
    admin.wait_for_confirmation(tx)
    return tx

@pytest.mark.testnet
def test_admin_tx3(
        admin: AdminNode,
        admin_s3: ChannelState,
        admin_tx3: Transaction,
        all_nodes: list[ElectionNode],
    ):
    assert isinstance(admin_tx3, Transaction)
    assert_node_state(admin, admin_s3)
    assert_nodes_in_sync(all_nodes)

@pytest.mark.testnet
def test_phase2_ceremony(
        admin, admin_s3, admin_tx3,
        guardian1, guardian1_s1, guardian1_tx1,
        guardian2, guardian2_s0,
        guardian3, guardian3_s0,
        device1, device1_s0,
        verifier1, verifier1_s0,
        all_nodes: list[ElectionNode],
    ):
    assert_nodes_in_sync(all_nodes)
    assert_node_state(admin, admin_s3)
    assert_node_state(guardian1, guardian1_s1)
    assert_node_state(guardian2, guardian2_s0)
    assert_node_state(guardian3, guardian3_s0)
    assert_node_state(device1, device1_s0)
    assert_node_state(verifier1, verifier1_s0)

# TODO test_phase3_voting goes here too, because admin doesn't post anything more first?


## ----------- admin_tx4 -----------

# This could be combined with posting the tally, but in later versions I think
# it would make more sense to have this be a definite stopping point where
# devices post any last votes and their STTs are burned (channels removed). So
# for now I'll keep it as an advance-only step.

@per_election_fixture
def admin_s4(
        admin_s3: ChannelState,
        static_phases,
    ) -> ChannelState:
    prev = admin_s3.state
    return AdminChannel(state=replace(
        prev,
        new_records = [],
        phase       = static_phases[4],
        seq         = 4,
    ))

@per_election_fixture
def admin_tx4(
        admin: AdminNode,
        admin_tx3: Transaction,
        static_phases,
    ) -> Transaction:
    tx = admin.advance_phase(static_phases[4])
    LOG.debug(f'admin_tx4: {tx}')
    admin.wait_for_confirmation(tx)
    return tx

@pytest.mark.testnet
def test_admin_tx4(
        admin: AdminNode,
        admin_s4: ChannelState,
        admin_tx4: Transaction,
        all_nodes: list[ElectionNode],
    ):
    assert isinstance(admin_tx4, Transaction)
    assert_nodes_in_sync(all_nodes)
    assert_node_state(admin, admin_s4)


## ----------- admin_tx5 -----------

@per_election_fixture
def admin_s5(
        admin_s4: ChannelState,
        static_transactions,
        static_phases,
    ) -> ChannelState:
    prev = admin_s4.state
    return AdminChannel(state=replace(
        prev,
        new_records = static_transactions['admin'][5][1],
        phase       = static_phases[5],
        seq         = 5,
    ))

@per_election_fixture
def admin_tx5(
        admin: AdminNode,
        admin_tx4: Transaction,
        static_transactions,
        static_phases,
    ) -> Transaction:
    tx = admin.post_public_records(
        new_records = static_transactions['admin'][5][1],
        new_phase   = static_phases[5],
    )
    LOG.debug(f'admin_tx5: {tx}')
    admin.wait_for_confirmation(tx)
    return tx

@pytest.mark.testnet
def test_admin_tx5(
        admin: AdminNode,
        admin_s5: ChannelState,
        admin_tx5: Transaction,
        all_nodes: list[ElectionNode],
    ):
    assert isinstance(admin_tx5, Transaction)
    assert_nodes_in_sync(all_nodes)
    assert_node_state(admin, admin_s5)


## ----------- admin_tx6 -----------

@per_election_fixture
def admin_s6(
        admin_s5: ChannelState,
        static_transactions,
        static_phases,
    ) -> ChannelState:
    prev = admin_s5.state
    return AdminChannel(state=replace(
        prev,
        new_records = static_transactions['admin'][6][1],
        phase       = static_phases[6],
        seq         = 6,
    ))

@per_election_fixture
def admin_tx6(
        admin: AdminNode,
        admin_tx5: Transaction,
        static_transactions,
        static_phases,
    ) -> Transaction:
    tx = admin.post_public_records(
        new_records = static_transactions['admin'][6][1],
        new_phase   = static_phases[6],
    )
    LOG.debug(f'admin_tx6: {tx}')
    admin.wait_for_confirmation(tx)
    return tx

@pytest.mark.testnet
def test_admin_tx6(
        admin: AdminNode,
        admin_s6: ChannelState,
        admin_tx6: Transaction,
        all_nodes: list[ElectionNode],
    ):
    assert isinstance(admin_tx6, Transaction)
    assert_nodes_in_sync(all_nodes)
    assert_node_state(admin, admin_s6)


## ----------- admin_tx7 -----------

@per_election_fixture
def admin_s7(
        admin_s6: ChannelState,
        static_transactions,
        static_phases,
    ) -> ChannelState:
    prev = admin_s6.state
    return AdminChannel(state=replace(
        prev,
        new_records = static_transactions['admin'][7][1],
        phase       = static_phases[7],
        seq         = 7,
    ))

@per_election_fixture
def admin_tx7(
        admin: AdminNode,
        admin_tx6: Transaction,
        static_transactions,
        static_phases,
    ) -> Transaction:
    tx = admin.post_public_records(
        new_records = static_transactions['admin'][7][1],
        new_phase   = static_phases[7],
    )
    LOG.debug(f'admin_tx7: {tx}')
    admin.wait_for_confirmation(tx)
    return tx

@pytest.mark.testnet
def test_admin_tx7(
        admin: AdminNode,
        admin_s7: ChannelState,
        admin_tx7: Transaction,
        all_nodes: list[ElectionNode],
    ):
    assert isinstance(admin_tx7, Transaction)
    assert_nodes_in_sync(all_nodes)
    assert_node_state(admin, admin_s7)


##  =================================
##  guardian1 transactions:
##  1. key ceremony round 1
##  2. key ceremony round 2
##  3. key ceremony round 3
##  4. decrypt results
##  5. summary (verification)
##  =================================

## ----------- guardian1_tx1 -----------

@per_election_fixture
def guardian1_s1(
        guardian1_s0: ChannelState,
        static_transactions,
    ) -> ChannelState:
    prev = guardian1_s0.state
    return SubChannel(state=replace(
        prev,
        new_records = static_transactions['guardian1'][1][1],
        seq = 1,
    ))

@per_election_fixture
def guardian1_tx1(
        admin_tx2: Transaction,
        guardian1: GuardianNode,
        static_transactions,
    ) -> Transaction:
    tx = guardian1.post_public_records(
        new_records = static_transactions['guardian1'][1][1],
    )
    LOG.debug(f'guardian1_tx1: {tx}')
    guardian1.wait_for_confirmation(tx)
    return tx

@pytest.mark.testnet
def test_guardian1_tx1(
        guardian1: GuardianNode,
        guardian1_s1: ChannelState,
        guardian1_tx1: Transaction,
        all_nodes: list[ElectionNode],
    ):
    assert isinstance(guardian1_tx1, Transaction)
    assert_node_state(guardian1, guardian1_s1)
    assert_nodes_in_sync(all_nodes)


## =================================
## final admin section:
## 8. rm subchannels
## 9. end election
## =================================

## ----------- admin_tx8 -----------

@per_election_fixture
def admin_s8(
        admin_s7: ChannelState,
        subchannel_ids,
        static_phases,
    ) -> ChannelState:
    prev = admin_s7.state
    remaining_ids = [i for i in prev.subchannels if not i in subchannel_ids]
    return AdminChannel(state=replace(
        prev,
        subchannels = remaining_ids,
        new_records = [],
        seq         = 8,
    ))

@per_election_fixture
def admin_tx8(
        admin_tx7: Transaction,
        admin: AdminNode,
        onboarding_info: dict[ChannelId, VerificationKeyHash],
    ) -> Transaction:
    sub_ids = list(onboarding_info.keys())
    ch_strs = [channel_id_to_string(k) for k in sub_ids]
    tx = admin.rm_subchannels(subchannels = sub_ids)
    LOG.debug(f'admin_tx8: {tx}')
    admin.wait_for_confirmation(tx)
    return tx

@pytest.mark.testnet
def test_admin_tx8(
        admin: AdminNode,
        admin_s8: ChannelState,
        admin_tx8: Transaction,
        all_nodes: list[ElectionNode],
    ):
    assert_node_state(admin, admin_s8)
    assert_nodes_in_sync(all_nodes)
