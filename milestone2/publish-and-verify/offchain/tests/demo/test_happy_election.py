import pytest
from dataclasses import replace
from pycardano import *
from egc import *
from helpers import *
import logging
import time

# Tests roughly match the ones here:
#
# onchain/tests/integration/happy_election.ak
#
# But now timing matters, so these offchain tests are ordered by phase rather
# than channel. Each phase has a "checkpoint" test at the end that ensures all
# nodes are in sync and that the pytest DAG runs the phases in order.


LOG = logging.getLogger(__name__)


## =================================
## 0. ConfigAnnouncePhase
## =================================

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
    # admin_tx0 is just the init_tx.
    # It's published by the funder and creates the admin STT.
    return init_tx

@pytest.mark.testnet
def test_admin_tx0(
        funder: FunderNode,
        admin: AdminNode,
        admin_s0: ChannelState,
        admin_tx0: Transaction,
    ):
    assert isinstance(admin_tx0, Transaction)

@pytest.mark.testnet
def test_phase0_announce(
        funder,
        admin, admin_s0, admin_tx0,
    ):
    assert_nodes_converge([
        (funder, None),
        (admin, admin_s0),
    ])


## =================================
## 1. ConfigOnboardingPhase
## =================================

@per_election_fixture
def admin_s1(
        admin_s0: ChannelState,
        static_transactions,
    ) -> ChannelState:
    prev = admin_s0.state
    return AdminChannel(state=replace(
        prev,
        new_records = static_transactions['admin'][1][1],
        phase       = ElectionConfigPhase(ConfigOnboardingPhase()),
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
        new_phase   = ElectionConfigPhase(ConfigOnboardingPhase()),
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
    assert_nodes_converge([
        (funder, None),
        (admin, admin_s1),
    ])

# TODO remove? not sure if we always want to depend on them individually
# From here on all 7 nodes can be started and should stay in sync.
# We'll confirm that at the end of each phase.
@per_election_fixture
def all_nodes(
        funder: FunderNode,
        admin: AdminNode,
        subchannel_nodes: list[ElectionNode],
    ) -> list[ElectionNode]:
    return [funder, admin] + subchannel_nodes

@pytest.mark.testnet
def test_phase1_onboarding(
        funder,
        admin, admin_s2, admin_tx2,
        guardian1, guardian1_s0,
        guardian2, guardian2_s0,
        guardian3, guardian3_s0,
        device1, device1_s0,
        verifier1, verifier1_s0,
        # all_nodes: list[ElectionNode],
    ):
    assert_nodes_converge([
        (funder   , None        ),
        (admin    , admin_s2    ),
        (guardian1, guardian1_s0),
        (guardian2, guardian2_s0),
        (guardian3, guardian3_s0),
        (device1  , device1_s0  ),
        (verifier1, verifier1_s0),
    ])
    assert_collateral([
        funder, admin,
        guardian1, guardian2, guardian3,
        device1, verifier1
    ])


## =================================
## 2. ConfigCeremonyPhase:
##    Round 1 (announce public keys)
##    Round 2 (secret share private keys)
##    Round 3 (confirm secret shares)
## =================================

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
        # static_phases,
    ) -> ChannelState:
    prev = admin_s1.state
    return AdminChannel(state=replace(
        prev,
        subchannels = subchannel_ids,
        new_records = [],
        phase       = ElectionConfigPhase(ConfigCeremonyPhase()),
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
        funder: FunderNode,
        admin: AdminNode,
        subchannel_nodes: list[ElectionNode],
        admin_s2: ChannelState,
        admin_tx2: Transaction,
        # all_nodes: list[ElectionNode],
    ):
    assert isinstance(admin_tx2, Transaction)
    expected = [
        (funder, None),
        (admin, admin_s2),
    ]
    for sub_node in subchannel_nodes:
        expected_state = sub_s0(sub_node.channel_id(), sub_node.publisher.wallet.vkh)
        expected.append((sub_node, expected_state))
    assert_nodes_converge(expected)


## =================================
## 3. ElectionVotingPhase
## =================================

@per_election_fixture
def admin_s3(
        admin_s2: ChannelState,
        static_transactions,
        # static_phases,
    ) -> ChannelState:
    prev = admin_s2.state
    return AdminChannel(state=replace(
        prev,
        new_records = static_transactions['admin'][3][1],
        phase       = ElectionVotingPhase(),
        seq         = 3,
    ))

@per_election_fixture
def admin_tx3(
        admin: AdminNode,
        admin_tx2: Transaction,
        static_transactions,
        # static_phases,
    ) -> Transaction:
    tx = admin.post_public_records(
        new_records = static_transactions['admin'][3][1],
        new_phase   = ElectionVotingPhase(),
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
    assert_nodes_converge([
        (n, admin_s3 if n == admin else None)
        for n in all_nodes
    ])

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
    assert_nodes_converge([
        (n, guardian1_s1 if n == guardian1 else None)
        for n in all_nodes
    ])

@pytest.mark.testnet
def test_phase2_ceremony(
        funder,
        admin, admin_s3, admin_tx3,
        guardian1, guardian1_s1, guardian1_tx1,
        guardian2, guardian2_s0,
        guardian3, guardian3_s0,
        device1, device1_s0,
        verifier1, verifier1_s0,
        all_nodes: list[ElectionNode],
    ):
    assert_nodes_converge([
        (funder   , None        ),
        (admin    , admin_s3    ),
        (guardian1, guardian1_s1), # TODO finish
        (guardian2, guardian2_s0), # TODO finish
        (guardian3, guardian3_s0), # TODO finish
        (device1  , device1_s0  ),
        (verifier1, verifier1_s0),
    ])


# TODO test_phase3_voting goes here too, because admin doesn't post anything more first?


## =================================
## 4. ResultsTallyPhase
## =================================

# This could be combined with posting the tally, but in later versions I think
# it would make more sense to have this be a definite stopping point where
# devices post any last votes and their STTs are burned (channels removed). So
# for now I'll keep it as an advance-only step.

@per_election_fixture
def admin_s4(
        admin_s3: ChannelState,
        # static_phases,
    ) -> ChannelState:
    prev = admin_s3.state
    return AdminChannel(state=replace(
        prev,
        new_records = [],
        phase       = ElectionResultsPhase(ResultsTallyPhase()),
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
    assert_nodes_converge([
        (n, admin_s4 if n == admin else None)
        for n in all_nodes
    ])


## =================================
## 5. ResultsDecryptPhase
## =================================

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
    assert_nodes_converge([
        (n, admin_s5 if n == admin else None)
        for n in all_nodes
    ])


## =================================
## 6. ElectionVerifyPhase
## =================================

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
    assert_nodes_converge([
        (n, admin_s6 if n == admin else None)
        for n in all_nodes
    ])


## =================================
## 7. ElectionFinalizePhase
## =================================

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
    assert_nodes_converge([
        (n, admin_s7 if n == admin else None)
        for n in all_nodes
    ])

@per_election_fixture
def admin_s8(
        admin_s7: ChannelState,
        subchannel_ids,
        # static_phases,
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
    assert_nodes_converge([
        (n, admin_s8 if n == admin else None)
        for n in all_nodes
    ])
