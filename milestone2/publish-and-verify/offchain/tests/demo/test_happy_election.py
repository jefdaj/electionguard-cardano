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
# than channel. Each phase has a "phaseN" test at the end that ensures all
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
        admin: AdminNode,
        admin_s0: ChannelState,
        admin_tx0: Transaction,
    ):
    test_tx(admin, admin_s0, admin_tx0)

@pytest.mark.testnet
def test_phase0_announce(
        admin, admin_s0, admin_tx0,
    ):
    assert_nodes_converge([
        (admin, admin_s0),
    ])


## =================================
## 1. ConfigOnboardingPhase
## =================================

@per_election_fixture
def admin_s1(
        admin_s0: ChannelState,
        static_transactions,
        static_phases,
    ) -> ChannelState:
    prev = admin_s0.state
    return AdminChannel(state=replace(
        prev,
        new_records = static_transactions['admin'][1][1],
        phase       = static_phases[1],
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
        new_phase = ElectionConfigPhase(ConfigOnboardingPhase()),
    )
    LOG.debug(f'admin_tx1: {tx}')
    admin.wait_for_confirmation(tx)
    return tx

@pytest.mark.testnet
def test_admin_tx1(admin, admin_s1, admin_tx1):
    test_tx(admin, admin_s1, admin_tx1)

# TODO remove? not sure if we always want to depend on them individually
# From here on all 7 nodes can be started and should stay in sync.
# We'll confirm that at the end of each phase.
@per_election_fixture
def all_nodes(
        admin: AdminNode,
        subchannel_nodes: list[ElectionNode],
    ) -> list[ElectionNode]:
    return [admin] + subchannel_nodes

@per_election_fixture
def onboarding_info(
        subchannel_nodes: list[ElectionNode],
    ) -> dict[ChannelId, VerificationKeyHash]:
    info = {
        n.channel_id() : n.publisher.wallet.vkh
        for n in subchannel_nodes
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
        phase       = static_phases[2],
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
        done_onboarding = True, # advance to ConfigCeremonyPhase
    )
    LOG.debug(f'admin_tx2: {tx}')
    admin.wait_for_confirmation(tx)
    return tx

@pytest.mark.testnet
def test_admin_tx2(admin, admin_s2, admin_tx2):
    test_tx(admin, admin_s2, admin_tx2)

@pytest.mark.testnet
def test_phase1_onboarding(
        admin    , admin_s2    , admin_tx2,
        guardian1, guardian1_s0,
        guardian2, guardian2_s0,
        guardian3, guardian3_s0,
        device1  , device1_s0  ,
        verifier1, verifier1_s0,
    ):
    assert_nodes_converge([
        (admin    , admin_s2    ),
        (guardian1, guardian1_s0),
        (guardian2, guardian2_s0),
        (guardian3, guardian3_s0),
        (device1  , device1_s0  ),
        (verifier1, verifier1_s0),
    ])
    assert_collateral([
        admin,
        guardian1, guardian2, guardian3,
        device1, verifier1
    ])


## =================================
## 2. ConfigCeremonyPhase:
##    - Round 1 (announce public keys)
##    - Round 2 (secret share private keys)
##    - Round 3 (confirm secret shares)
## =================================

# These two functions turn out to be reasonably generic;
# they'll be used in all the simple post_public_records
# continuations from now on.

def post_state(
        static_transactions,
        prev_state: ChannelState,
        role_name: str,
        role_index: int,
        tx_index: int, # seq and also index in static_transactions
        ) -> ChannelState:
    ch_str = role_name + str(role_index)
    records = static_transactions[ch_str][tx_index][1]
    LOG.debug(f'{ch_str}_s{tx_index} records: {records}')
    assert isinstance(records, list)
    return SubChannel(state=replace(
        prev_state.state,
        new_records = records,
        seq = tx_index,
    ))

def post_tx(
        static_transactions,
        node_: ElectionNode,
        tx_index: int, # index in static_transactions
    ) -> Transaction:
    ch_str = node_.channel_str()
    (_, recs) = static_transactions[ch_str][tx_index]
    tx = node_.post_public_records(new_records=recs)
    LOG.debug(f'{ch_str}_tx{tx_index}: {tx}')
    node_.wait_for_confirmation(tx)
    return tx

## ----------- Round 1 -----------

@per_election_fixture
def guardian1_s1(guardian1_s0, static_transactions) -> ChannelState:
    return post_state(static_transactions, guardian1_s0, 'guardian', 1, 1)

@per_election_fixture
def guardian2_s1(guardian2_s0, static_transactions) -> ChannelState:
    return post_state(static_transactions, guardian2_s0, 'guardian', 2, 1)

@per_election_fixture
def guardian3_s1(guardian3_s0, static_transactions) -> ChannelState:
    return post_state(static_transactions, guardian3_s0, 'guardian', 3, 1)

@per_election_fixture
def guardian1_tx1(admin_tx2, guardian1, static_transactions):
    return post_tx(static_transactions, guardian1, 1)

@per_election_fixture
def guardian2_tx1(admin_tx2, guardian2, static_transactions):
    return post_tx(static_transactions, guardian2, 1)

@per_election_fixture
def guardian3_tx1(admin_tx2, guardian3, static_transactions):
    return post_tx(static_transactions, guardian3, 1)

@pytest.mark.testnet
def test_guardian1_tx1(guardian1, guardian1_s1, guardian1_tx1):
    test_tx(guardian1, guardian1_s1, guardian1_tx1)

@pytest.mark.testnet
def test_guardian2_tx1(guardian2, guardian2_s1, guardian2_tx1):
    test_tx(guardian2, guardian2_s1, guardian2_tx1)

@pytest.mark.testnet
def test_guardian3_tx1(guardian3, guardian3_s1, guardian3_tx1):
    test_tx(guardian3, guardian3_s1, guardian3_tx1)

@pytest.mark.testnet
def test_phase2_ceremony_round1(
        admin    , admin_s2    , admin_tx2    ,
        guardian1, guardian1_s1, guardian1_tx1,
        guardian2, guardian2_s1, guardian2_tx1,
        guardian3, guardian3_s1, guardian3_tx1,
        device1  , device1_s0  ,
        verifier1, verifier1_s0,
    ):
    assert_nodes_converge([
        (admin    , admin_s2    ),
        (guardian1, guardian1_s1),
        (guardian2, guardian2_s1),
        (guardian3, guardian3_s1),
        (device1  , device1_s0  ),
        (verifier1, verifier1_s0),
    ])


## ----------- Round 2 -----------

@per_election_fixture
def guardian1_s2(guardian1_s0, static_transactions) -> ChannelState:
    return post_state(static_transactions, guardian1_s0, 'guardian', 1, 2)

@per_election_fixture
def guardian2_s2(guardian2_s0, static_transactions) -> ChannelState:
    return post_state(static_transactions, guardian2_s0, 'guardian', 2, 2)

@per_election_fixture
def guardian3_s2(guardian3_s0, static_transactions) -> ChannelState:
    return post_state(static_transactions, guardian3_s0, 'guardian', 3, 2)

@per_election_fixture
def guardian1_tx2(guardian1_tx1, guardian1, static_transactions):
    return post_tx(static_transactions, guardian1, 2)

@per_election_fixture
def guardian2_tx2(guardian2_tx1, guardian2, static_transactions):
    return post_tx(static_transactions, guardian2, 2)

@per_election_fixture
def guardian3_tx2(guardian3_tx1, guardian3, static_transactions):
    return post_tx(static_transactions, guardian3, 2)

@pytest.mark.testnet
def test_guardian1_tx2(guardian1, guardian1_s2, guardian1_tx2):
    test_tx(guardian1, guardian1_s2, guardian1_tx2)

@pytest.mark.testnet
def test_guardian2_tx2(guardian2, guardian2_s2, guardian2_tx2):
    test_tx(guardian2, guardian2_s2, guardian2_tx2)

@pytest.mark.testnet
def test_guardian3_tx2(guardian3, guardian3_s2, guardian3_tx2):
    test_tx(guardian3, guardian3_s2, guardian3_tx2)

@pytest.mark.testnet
def test_phase2_ceremony_round2(
        admin    , admin_s2    ,
        guardian1, guardian1_s2, guardian1_tx2,
        guardian2, guardian2_s2, guardian2_tx2,
        guardian3, guardian3_s2, guardian3_tx2,
        device1  , device1_s0  ,
        verifier1, verifier1_s0,
    ):
    assert_nodes_converge([
        (admin    , admin_s2    ),
        (guardian1, guardian1_s2),
        (guardian2, guardian2_s2),
        (guardian3, guardian3_s2),
        (device1  , device1_s0  ),
        (verifier1, verifier1_s0),
    ])


## ----------- Round 3 -----------

@per_election_fixture
def guardian1_s3(guardian1_s0, static_transactions) -> ChannelState:
    return post_state(static_transactions, guardian1_s0, 'guardian', 1, 3)

@per_election_fixture
def guardian2_s3(guardian2_s0, static_transactions) -> ChannelState:
    return post_state(static_transactions, guardian2_s0, 'guardian', 2, 3)

@per_election_fixture
def guardian3_s3(guardian3_s0, static_transactions) -> ChannelState:
    return post_state(static_transactions, guardian3_s0, 'guardian', 3, 3)

@per_election_fixture
def guardian1_tx3(guardian1_tx2, guardian1, static_transactions):
    return post_tx(static_transactions, guardian1, 3)

@per_election_fixture
def guardian2_tx3(guardian2_tx2, guardian2, static_transactions):
    return post_tx(static_transactions, guardian2, 3)

@per_election_fixture
def guardian3_tx3(guardian3_tx2, guardian3, static_transactions):
    return post_tx(static_transactions, guardian3, 3)

@pytest.mark.testnet
def test_guardian1_tx3(guardian1, guardian1_s3, guardian1_tx3):
    test_tx(guardian1, guardian1_s3, guardian1_tx3)

@pytest.mark.testnet
def test_guardian2_tx3(guardian2, guardian2_s3, guardian2_tx3):
    test_tx(guardian2, guardian2_s3, guardian2_tx3)

@pytest.mark.testnet
def test_guardian3_tx3(guardian3, guardian3_s3, guardian3_tx3):
    test_tx(guardian3, guardian3_s3, guardian3_tx3)

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

# After the guardian backups are all confirmed, admin can publish the final
# voting config and advance to voting phase.
# TODO should there be a separate little phase for this step?
@per_election_fixture
def admin_tx3(
        admin: AdminNode,
        admin_tx2: Transaction,
        guardian1_tx3: Transaction,
        guardian2_tx3: Transaction,
        guardian3_tx3: Transaction,
        static_transactions,
    ) -> Transaction:
    tx = admin.post_public_records(
        new_records = static_transactions['admin'][3][1],
        new_phase = ElectionVotingPhase(),
    )
    LOG.debug(f'admin_tx3: {tx}')
    admin.wait_for_confirmation(tx)
    return tx

@pytest.mark.testnet
def test_admin_tx3(admin, admin_s3, admin_tx3):
    test_tx(admin, admin_s3, admin_tx3)

@pytest.mark.testnet
def test_phase2_ceremony_round3(
        admin    , admin_s3    , admin_tx3,
        guardian1, guardian1_s3, guardian1_tx3,
        guardian2, guardian2_s3, guardian2_tx3,
        guardian3, guardian3_s3, guardian3_tx3,
        device1  , device1_s0  ,
        verifier1, verifier1_s0,
    ):
    assert_nodes_converge([
        (admin    , admin_s3    ),
        (guardian1, guardian1_s3),
        (guardian2, guardian2_s3),
        (guardian3, guardian3_s3),
        (device1  , device1_s0  ),
        (verifier1, verifier1_s0),
    ])

## =================================
## 3. ElectionVotingPhase
## =================================

@per_election_fixture
def device1_s1(device1_s0, static_transactions) -> ChannelState:
    return post_state(static_transactions, device1_s0, 'device', 1, 1)

@per_election_fixture
def device1_s2(device1_s1, static_transactions) -> ChannelState:
    return post_state(static_transactions, device1_s1, 'device', 1, 2)

@per_election_fixture
def device1_s3(device1_s2, static_transactions) -> ChannelState:
    return post_state(static_transactions, device1_s2, 'device', 1, 3)

@per_election_fixture
def device1_tx1(admin_tx2, device1, static_transactions):
    return post_tx(static_transactions, device1, 1)

@per_election_fixture
def device1_tx2(device1_tx1, device1, static_transactions):
    return post_tx(static_transactions, device1, 2)

@per_election_fixture
def device1_tx3(admin_tx2, device1, static_transactions):
    return post_tx(static_transactions, device1, 3)

@pytest.mark.testnet
def test_phase3_voting(
        admin    , admin_s3    , admin_tx3,
        guardian1, guardian1_s3,
        guardian2, guardian2_s3,
        guardian3, guardian3_s3,
        device1  , device1_s3  , device1_tx3,
        verifier1, verifier1_s0,
    ):
    assert_nodes_converge([
        (admin    , admin_s3    ),
        (guardian1, guardian1_s3),
        (guardian2, guardian2_s3),
        (guardian3, guardian3_s3),
        (device1  , device1_s3  ),
        (verifier1, verifier1_s0),
    ])


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
    ) -> Transaction:
    tx = admin.advance_phase(
        ElectionResultsPhase(ResultsTallyPhase())
    )
    LOG.debug(f'admin_tx4: {tx}')
    admin.wait_for_confirmation(tx)
    return tx

@pytest.mark.testnet
def test_admin_tx4(admin, admin_s4, admin_tx4):
    test_tx(admin, admin_s4, admin_tx4)

@pytest.mark.testnet
def test_phase4_tally(
        admin    , admin_s4    , admin_tx4,
        guardian1, guardian1_s3,
        guardian2, guardian2_s3,
        guardian3, guardian3_s3,
        device1  , device1_s3  ,
        verifier1, verifier1_s0,
    ):
    assert_nodes_converge([
        (admin    , admin_s4    ),
        (guardian1, guardian1_s3),
        (guardian2, guardian2_s3),
        (guardian3, guardian3_s3),
        (device1  , device1_s3  ),
        (verifier1, verifier1_s0),
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
    ) -> Transaction:
    tx = admin.post_public_records(
        new_records = static_transactions['admin'][5][1],
        new_phase = ElectionResultsPhase(ResultsDecryptPhase()),
    )
    LOG.debug(f'admin_tx5: {tx}')
    admin.wait_for_confirmation(tx)
    return tx

@pytest.mark.testnet
def test_admin_tx5(admin, admin_s5, admin_tx5):
    test_tx(admin, admin_s5, admin_tx5)

@pytest.mark.testnet
def test_phase5_decrypt(
        admin    , admin_s5    , admin_tx5,
        guardian1, guardian1_s3,
        guardian2, guardian2_s3,
        guardian3, guardian3_s3,
        device1  , device1_s3  ,
        verifier1, verifier1_s0,
    ):
    assert_nodes_converge([
        (admin    , admin_s5    ),
        (guardian1, guardian1_s3),
        (guardian2, guardian2_s3),
        (guardian3, guardian3_s3),
        (device1  , device1_s3  ),
        (verifier1, verifier1_s0),
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
    ) -> Transaction:
    tx = admin.post_public_records(
        new_records = static_transactions['admin'][6][1],
        new_phase = ElectionVerifyPhase(),
    )
    LOG.debug(f'admin_tx6: {tx}')
    admin.wait_for_confirmation(tx)
    return tx

@pytest.mark.testnet
def test_admin_tx6(admin, admin_s6, admin_tx6):
    test_tx(admin, admin_s6, admin_tx6)

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

# Admin post summary (verification) of election and advance to finalize phase.
# TODO should this come before, after, or same time as others post theirs?
# TODO extra commit reveal step for verifications?
@per_election_fixture
def admin_tx7(
        admin: AdminNode,
        admin_tx6: Transaction,
        static_transactions,
    ) -> Transaction:
    tx = admin.post_public_records(
        new_records = static_transactions['admin'][7][1],
        new_phase = ElectionFinalizePhase(),
    )
    LOG.debug(f'admin_tx7: {tx}')
    admin.wait_for_confirmation(tx)
    return tx

@pytest.mark.testnet
def test_admin_tx7(admin, admin_s7, admin_tx7):
    test_tx(admin, admin_s7, admin_tx7)

@pytest.mark.testnet
def test_phase6_verify(
        admin    , admin_s7    , admin_tx7,
        guardian1, guardian1_s3,
        guardian2, guardian2_s3,
        guardian3, guardian3_s3,
        device1  , device1_s3  ,
        verifier1, verifier1_s0,
    ):
    assert_nodes_converge([
        (admin    , admin_s7    ),
        (guardian1, guardian1_s3),
        (guardian2, guardian2_s3),
        (guardian3, guardian3_s3),
        (device1  , device1_s3  ),
        (verifier1, verifier1_s0),
    ])


## =================================
## 7. ElectionFinalizePhase:
##    - RmSubChannels
##    - EndElection
## =================================

@per_election_fixture
def admin_s8(
        admin_s7: ChannelState,
        subchannel_ids,
    ) -> ChannelState:
    prev = admin_s7.state
    remaining_ids = [i for i in prev.subchannels if not i in subchannel_ids]
    return AdminChannel(state=replace(
        prev,
        subchannels = remaining_ids,
        new_records = [],
        seq         = 8,
    ))

# TODO update guardian txs as you write the later ones
# TODO and add device1 + verifier1
@per_election_fixture
def admin_tx8(
        admin: AdminNode,
        onboarding_info: dict[ChannelId, VerificationKeyHash],
        admin_tx7: Transaction,
        guardian1_tx1: Transaction,
        guardian2_tx1: Transaction,
        guardian3_tx1: Transaction,
    ) -> Transaction:
    sub_ids = list(onboarding_info.keys())
    ch_strs = [channel_id_to_string(k) for k in sub_ids]
    tx = admin.rm_subchannels(subchannels = sub_ids)
    LOG.debug(f'admin_tx8: {tx}')
    admin.wait_for_confirmation(tx)
    return tx

@pytest.mark.testnet
def test_admin_tx8(admin, admin_s8, admin_tx8):
    test_tx(admin, admin_s8, admin_tx8)

@pytest.mark.testnet
def test_phase7_finalize(
        admin, admin_s8, admin_tx8,
        guardian1, guardian2, guardian3, device1, verifier1,
    ):
    # TODO move this to test_admin_tx8 above and test that admin also None here?
    assert_nodes_converge([
        (admin    , admin_s8),
        (guardian1, None    ),
        (guardian2, None    ),
        (guardian3, None    ),
        (device1  , None    ),
        (verifier1, None    ),
    ])

# TODO or, separate test for tx9 here?
