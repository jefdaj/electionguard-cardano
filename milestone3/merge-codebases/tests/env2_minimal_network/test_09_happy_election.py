import pytest
from dataclasses import replace
from pycardano import *
from egc import *
from ..lib import *
from .lib import *
# from data.static_records import *
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

@pytest.fixture(scope='module')
def admin_s0(admin_vkh: VerificationKeyHash) -> ChannelState:
    return AdminChannel(state=AdminChannelState(
        admin       = admin_vkh.payload,
        ipfs_node   = NoIpfsNode(),
        subchannels = [],
        new_records = [],
        phase       = ElectionConfigPhase(ConfigAnnouncePhase()),
        seq         = 0,
    ))

@pytest.fixture(scope='module')
def admin_tx0(init_tx: Transaction) -> Transaction:
    # admin_tx0 is just the init_tx.
    # It's published by the funder and creates the admin STT.
    return init_tx

def test_admin_tx0(
        admin: AdminNode,
        admin_s0: ChannelState,
        admin_tx0: Transaction,
    ):
    assert_tx(admin, admin_s0, admin_tx0)

def test_phase0_announce(
        admin, admin_s0, admin_tx0,
    ):
    assert_nodes_converge([
        (admin, admin_s0),
    ], EgcPhase.CONFIG_ANNOUNCE)


## =================================
## 1. ConfigOnboardingPhase
## =================================

@pytest.fixture(scope='module')
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

@pytest.fixture(scope='module')
def admin_tx1(
        admin: AdminNode,
        admin_tx0: Transaction,
        static_transactions,
        static_files_dir,
    ) -> Transaction:
    pairs = load_static_record_pairs(static_transactions['admin'][1][1], static_files_dir)
    tx = admin.post_public_records(
        new_record_pairs = pairs,
        new_phase = ElectionConfigPhase(ConfigOnboardingPhase()),
    )
    LOG.debug(f'admin_tx1: {tx}')
    admin.await_tx_confirmed(tx)
    return tx

def test_admin_tx1(admin, admin_s1, admin_tx1):
    assert_tx(admin, admin_s1, admin_tx1)

# TODO remove? not sure if we always want to depend on them individually
# From here on all 7 nodes can be started and should stay in sync.
# We'll confirm that at the end of each phase.
@pytest.fixture(scope='module')
def all_nodes(
        admin: AdminNode,
        subchannel_nodes: list[ElectionNode],
    ) -> list[ElectionNode]:
    return [admin] + subchannel_nodes

@pytest.fixture(scope='module')
def onboarding_info(
        subchannel_nodes: list[ElectionNode],
    ) -> dict[ChannelId, VerificationKeyHash]:
    info = {
        n.channel_id() : n.publisher.wallet.vkh
        for n in subchannel_nodes
    }
    return info

@pytest.fixture(scope='module')
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

@pytest.fixture(scope='module')
def admin_tx2(
        admin_tx1: Transaction,
        admin: AdminNode,
        onboarding_info: dict[ChannelId, VerificationKeyHash],
    ) -> Transaction:
    ch_strs = [channel_id_to_string(k) for k in onboarding_info.keys()]
    LOG.info(f'admin got onboarding info from {', '.join(ch_strs)}')
    tx = admin.add_subchannels(
        subchannels = onboarding_info,
        subchannel_ada = 20,
        done_onboarding = True, # advance to ConfigCeremonyPhase
    )
    LOG.debug(f'admin_tx2: {tx}')
    admin.await_tx_confirmed(tx)
    return tx

def test_admin_tx2(admin, admin_s2, admin_tx2):
    assert_tx(admin, admin_s2, admin_tx2)

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
    ], EgcPhase.CONFIG_CEREMONY_ROUND1)
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
        static_transactions, static_files_dir,
        node_: ElectionNode,
        tx_index: int, # index in static_transactions
    ) -> Transaction:
    ch_str = node_.channel_str()
    (_, recs) = static_transactions[ch_str][tx_index]
    pairs = load_static_record_pairs(recs, static_files_dir)
    tx = node_.post_public_records(new_record_pairs=pairs)
    LOG.debug(f'{ch_str}_tx{tx_index}: {tx}')
    node_.await_tx_confirmed(tx)
    return tx

## ----------- Round 1 -----------

@pytest.fixture(scope='module')
def guardian1_s1(guardian1_s0, static_transactions) -> ChannelState:
    return post_state(static_transactions, guardian1_s0, 'guardian', 1, 1)

@pytest.fixture(scope='module')
def guardian2_s1(guardian2_s0, static_transactions) -> ChannelState:
    return post_state(static_transactions, guardian2_s0, 'guardian', 2, 1)

@pytest.fixture(scope='module')
def guardian3_s1(guardian3_s0, static_transactions) -> ChannelState:
    return post_state(static_transactions, guardian3_s0, 'guardian', 3, 1)

@pytest.fixture(scope='module')
def guardian1_tx1(admin_tx2, guardian1, static_transactions, static_files_dir):
    return post_tx(static_transactions, static_files_dir, guardian1, 1)

@pytest.fixture(scope='module')
def guardian2_tx1(admin_tx2, guardian2, static_transactions, static_files_dir):
    return post_tx(static_transactions, static_files_dir, guardian2, 1)

@pytest.fixture(scope='module')
def guardian3_tx1(admin_tx2, guardian3, static_transactions, static_files_dir):
    return post_tx(static_transactions, static_files_dir, guardian3, 1)

def test_guardian1_tx1(guardian1, guardian1_s1, guardian1_tx1):
    assert_tx(guardian1, guardian1_s1, guardian1_tx1)

def test_guardian2_tx1(guardian2, guardian2_s1, guardian2_tx1):
    assert_tx(guardian2, guardian2_s1, guardian2_tx1)

def test_guardian3_tx1(guardian3, guardian3_s1, guardian3_tx1):
    assert_tx(guardian3, guardian3_s1, guardian3_tx1)

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
    ], EgcPhase.CONFIG_CEREMONY_ROUND2)


## ----------- Round 2 -----------

@pytest.fixture(scope='module')
def guardian1_s2(guardian1_s0, static_transactions) -> ChannelState:
    return post_state(static_transactions, guardian1_s0, 'guardian', 1, 2)

@pytest.fixture(scope='module')
def guardian2_s2(guardian2_s0, static_transactions) -> ChannelState:
    return post_state(static_transactions, guardian2_s0, 'guardian', 2, 2)

@pytest.fixture(scope='module')
def guardian3_s2(guardian3_s0, static_transactions) -> ChannelState:
    return post_state(static_transactions, guardian3_s0, 'guardian', 3, 2)

@pytest.fixture(scope='module')
def guardian1_tx2(guardian1_tx1, guardian1, static_transactions, static_files_dir):
    return post_tx(static_transactions, static_files_dir, guardian1, 2)

@pytest.fixture(scope='module')
def guardian2_tx2(guardian2_tx1, guardian2, static_transactions, static_files_dir):
    return post_tx(static_transactions, static_files_dir, guardian2, 2)

@pytest.fixture(scope='module')
def guardian3_tx2(guardian3_tx1, guardian3, static_transactions, static_files_dir):
    return post_tx(static_transactions, static_files_dir, guardian3, 2)

def test_guardian1_tx2(guardian1, guardian1_s2, guardian1_tx2):
    assert_tx(guardian1, guardian1_s2, guardian1_tx2)

def test_guardian2_tx2(guardian2, guardian2_s2, guardian2_tx2):
    assert_tx(guardian2, guardian2_s2, guardian2_tx2)

def test_guardian3_tx2(guardian3, guardian3_s2, guardian3_tx2):
    assert_tx(guardian3, guardian3_s2, guardian3_tx2)

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
    ], EgcPhase.CONFIG_CEREMONY_ROUND3)


## ----------- Round 3 -----------

@pytest.fixture(scope='module')
def guardian1_s3(guardian1_s0, static_transactions) -> ChannelState:
    return post_state(static_transactions, guardian1_s0, 'guardian', 1, 3)

@pytest.fixture(scope='module')
def guardian2_s3(guardian2_s0, static_transactions) -> ChannelState:
    return post_state(static_transactions, guardian2_s0, 'guardian', 2, 3)

@pytest.fixture(scope='module')
def guardian3_s3(guardian3_s0, static_transactions) -> ChannelState:
    return post_state(static_transactions, guardian3_s0, 'guardian', 3, 3)

@pytest.fixture(scope='module')
def guardian1_tx3(guardian1_tx2, guardian1, static_transactions, static_files_dir):
    return post_tx(static_transactions, static_files_dir, guardian1, 3)

@pytest.fixture(scope='module')
def guardian2_tx3(guardian2_tx2, guardian2, static_transactions, static_files_dir):
    return post_tx(static_transactions, static_files_dir, guardian2, 3)

@pytest.fixture(scope='module')
def guardian3_tx3(guardian3_tx2, guardian3, static_transactions, static_files_dir):
    return post_tx(static_transactions, static_files_dir, guardian3, 3)

def test_guardian1_tx3(guardian1, guardian1_s3, guardian1_tx3):
    assert_tx(guardian1, guardian1_s3, guardian1_tx3)

def test_guardian2_tx3(guardian2, guardian2_s3, guardian2_tx3):
    assert_tx(guardian2, guardian2_s3, guardian2_tx3)

def test_guardian3_tx3(guardian3, guardian3_s3, guardian3_tx3):
    assert_tx(guardian3, guardian3_s3, guardian3_tx3)

@pytest.fixture(scope='module')
def device1_s1(device1_s0, static_transactions) -> ChannelState:
    return post_state(static_transactions, device1_s0, 'device', 1, 1)

@pytest.fixture(scope='module')
def device1_tx1(admin_tx2, device1, static_transactions, static_files_dir):
    return post_tx(static_transactions, static_files_dir, device1, 1)

def test_device1_tx1(device1, device1_s1, device1_tx1):
    assert_tx(device1, device1_s1, device1_tx1)

@pytest.fixture(scope='module')
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
# voting config and advance to voting phase. Voting devices should probably
# also be announced by this point, although not technically required.
# TODO should there be a separate little phase for this step?
@pytest.fixture(scope='module')
def admin_tx3(
        admin: AdminNode,
        admin_tx2: Transaction,
        guardian1_tx3: Transaction,
        guardian2_tx3: Transaction,
        guardian3_tx3: Transaction,
        device1_tx1: Transaction,
        static_transactions, static_files_dir,
    ) -> Transaction:
    pairs = load_static_record_pairs(static_transactions['admin'][3][1], static_files_dir)
    tx = admin.post_public_records(
        new_record_pairs = pairs,
        new_phase = ElectionVotingPhase(),
    )
    LOG.debug(f'admin_tx3: {tx}')
    admin.await_tx_confirmed(tx)
    return tx

def test_admin_tx3(admin, admin_s3, admin_tx3):
    assert_tx(admin, admin_s3, admin_tx3)

def test_phase2_ceremony_round3(
        admin    , admin_s3    , admin_tx3,
        guardian1, guardian1_s3, guardian1_tx3,
        guardian2, guardian2_s3, guardian2_tx3,
        guardian3, guardian3_s3, guardian3_tx3,
        device1  , device1_s1  , device1_tx1,
        verifier1, verifier1_s0,
    ):
    assert_nodes_converge([
        (admin    , admin_s3    ),
        (guardian1, guardian1_s3),
        (guardian2, guardian2_s3),
        (guardian3, guardian3_s3),
        (device1  , device1_s1  ),
        (verifier1, verifier1_s0),
    ], EgcPhase.VOTING)

## =================================
## 3. ElectionVotingPhase
## =================================

@pytest.fixture(scope='module')
def device1_s2(device1_s1, static_transactions) -> ChannelState:
    return post_state(static_transactions, device1_s1, 'device', 1, 2)

@pytest.fixture(scope='module')
def device1_s3(device1_s2, static_transactions) -> ChannelState:
    return post_state(static_transactions, device1_s2, 'device', 1, 3)

@pytest.fixture(scope='module')
def device1_tx2(device1_tx1, device1, static_transactions, static_files_dir):
    return post_tx(static_transactions, static_files_dir, device1, 2)

@pytest.fixture(scope='module')
def device1_tx3(device1_tx2, device1, static_transactions, static_files_dir):
    return post_tx(static_transactions, static_files_dir, device1, 3)

def test_device1_tx2(device1, device1_s2, device1_tx2):
    assert_tx(device1, device1_s2, device1_tx2)

def test_device1_tx3(device1, device1_s3, device1_tx3):
    assert_tx(device1, device1_s3, device1_tx3)

# This could be combined with posting the tally, but in later versions I think
# it would make more sense to have this be a definite stopping point where
# devices post any last votes and their STTs are burned (channels removed). So
# for now I'll keep it as an advance-only step.

@pytest.fixture(scope='module')
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

@pytest.fixture(scope='module')
def admin_tx4(
        admin: AdminNode,
        admin_tx3: Transaction,
    ) -> Transaction:
    tx = admin.advance_phase(
        ElectionResultsPhase(ResultsTallyPhase())
    )
    LOG.debug(f'admin_tx4: {tx}')
    admin.await_tx_confirmed(tx)
    return tx

def test_admin_tx4(admin, admin_s4, admin_tx4):
    assert_tx(admin, admin_s4, admin_tx4)

def test_phase3_voting(
        admin    , admin_s4    , admin_tx4,
        guardian1, guardian1_s3,
        guardian2, guardian2_s3,
        guardian3, guardian3_s3,
        device1  , device1_s3  , device1_tx3,
        verifier1, verifier1_s0,
    ):
    assert_nodes_converge([
        (admin    , admin_s4    ),
        (guardian1, guardian1_s3),
        (guardian2, guardian2_s3),
        (guardian3, guardian3_s3),
        (device1  , device1_s3  ),
        (verifier1, verifier1_s0),
    ], EgcPhase.RESULTS_TALLY)


## =================================
## 4. ResultsTallyPhase
## =================================

@pytest.fixture(scope='module')
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

@pytest.fixture(scope='module')
def admin_tx5(
        admin: AdminNode,
        admin_tx4: Transaction,
        static_transactions, static_files_dir,
    ) -> Transaction:
    pairs = load_static_record_pairs(static_transactions['admin'][5][1], static_files_dir)
    tx = admin.post_public_records(
        new_record_pairs = pairs,
        new_phase = ElectionResultsPhase(ResultsDecryptPhase()),
    )
    LOG.debug(f'admin_tx5: {tx}')
    admin.await_tx_confirmed(tx)
    return tx

def test_admin_tx5(admin, admin_s5, admin_tx5):
    assert_tx(admin, admin_s5, admin_tx5)

@pytest.fixture(scope='module')
def guardian1_s4(guardian1_s3, static_transactions) -> ChannelState:
    return post_state(static_transactions, guardian1_s3, 'guardian', 1, 4)

@pytest.fixture(scope='module')
def guardian2_s4(guardian2_s3, static_transactions) -> ChannelState:
    return post_state(static_transactions, guardian2_s3, 'guardian', 2, 4)

@pytest.fixture(scope='module')
def guardian3_s4(guardian3_s3, static_transactions) -> ChannelState:
    return post_state(static_transactions, guardian3_s3, 'guardian', 3, 4)

@pytest.fixture(scope='module')
def guardian1_tx4(guardian1_tx3, admin_tx5, guardian1, static_transactions, static_files_dir):
    return post_tx(static_transactions, static_files_dir, guardian1, 4)

@pytest.fixture(scope='module')
def guardian2_tx4(guardian2_tx3, admin_tx5, guardian2, static_transactions, static_files_dir):
    return post_tx(static_transactions, static_files_dir, guardian2, 4)

@pytest.fixture(scope='module')
def guardian3_tx4(guardian3_tx3, admin_tx5, guardian3, static_transactions, static_files_dir):
    return post_tx(static_transactions, static_files_dir, guardian3, 4)

def test_guardian1_tx4(guardian1, guardian1_s3, guardian1_tx4):
    assert_tx(guardian1, guardian1_s3, guardian1_tx4)

def test_guardian2_tx4(guardian2, guardian2_s3, guardian2_tx4):
    assert_tx(guardian2, guardian2_s3, guardian2_tx4)

def test_guardian3_tx4(guardian3, guardian3_s3, guardian3_tx4):
    assert_tx(guardian3, guardian3_s3, guardian3_tx4)

def test_phase4_tally(
        admin    , admin_s5    , admin_tx5,
        guardian1, guardian1_s4, guardian1_tx4,
        guardian2, guardian2_s4, guardian2_tx4,
        guardian3, guardian3_s4, guardian3_tx4,
        device1  , device1_s3  ,
        verifier1, verifier1_s0,
    ):
    assert_nodes_converge([
        (admin    , admin_s5    ),
        (guardian1, guardian1_s4),
        (guardian2, guardian2_s4),
        (guardian3, guardian3_s4),
        (device1  , device1_s3  ),
        (verifier1, verifier1_s0),
    ], EgcPhase.RESULTS_DECRYPT)


## =================================
## 5. ResultsDecryptPhase
## =================================

@pytest.fixture(scope='module')
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

@pytest.fixture(scope='module')
def admin_tx6(
        admin: AdminNode,
        admin_tx5: Transaction,
        static_transactions, static_files_dir,
    ) -> Transaction:
    pairs = load_static_record_pairs(static_transactions['admin'][6][1], static_files_dir)
    tx = admin.post_public_records(
        new_record_pairs = pairs,
        new_phase = ElectionVerifyPhase(),
    )
    LOG.debug(f'admin_tx6: {tx}')
    admin.await_tx_confirmed(tx)
    return tx

def test_admin_tx6(admin, admin_s6, admin_tx6):
    assert_tx(admin, admin_s6, admin_tx6)

def test_phase5_decrypt(
        admin    , admin_s6    , admin_tx6,
        guardian1, guardian1_s4,
        guardian2, guardian2_s4,
        guardian3, guardian3_s4,
        device1  , device1_s3  ,
        verifier1, verifier1_s0,
    ):
    assert_nodes_converge([
        (admin    , admin_s6    ),
        (guardian1, guardian1_s4),
        (guardian2, guardian2_s4),
        (guardian3, guardian3_s4),
        (device1  , device1_s3  ),
        (verifier1, verifier1_s0),
    ], EgcPhase.VERIFY)


## =================================
## 6. ElectionVerifyPhase
## =================================

@pytest.fixture(scope='module')
def guardian1_s5(guardian1_s4, static_transactions):
    return post_state(static_transactions, guardian1_s4, 'guardian', 1, 5)

@pytest.fixture(scope='module')
def guardian2_s5(guardian2_s4, static_transactions):
    return post_state(static_transactions, guardian2_s4, 'guardian', 2, 5)

@pytest.fixture(scope='module')
def guardian3_s5(guardian3_s4, static_transactions):
    return post_state(static_transactions, guardian3_s4, 'guardian', 3, 5)

@pytest.fixture(scope='module')
def guardian1_tx5(guardian1_tx4, guardian1, static_transactions, static_files_dir):
    return post_tx(static_transactions, static_files_dir, guardian1, 5)

@pytest.fixture(scope='module')
def guardian2_tx5(guardian2_tx4, guardian2, static_transactions, static_files_dir):
    return post_tx(static_transactions, static_files_dir, guardian2, 5)

@pytest.fixture(scope='module')
def guardian3_tx5(guardian3_tx4, guardian3, static_transactions, static_files_dir):
    return post_tx(static_transactions, static_files_dir, guardian3, 5)

def test_guardian1_tx5(guardian1, guardian1_s4, guardian1_tx5):
    assert_tx(guardian1, guardian1_s4, guardian1_tx5)

def test_guardian2_tx5(guardian2, guardian2_s4, guardian2_tx5):
    assert_tx(guardian2, guardian2_s4, guardian2_tx5)

def test_guardian3_tx5(guardian3, guardian3_s4, guardian3_tx5):
    assert_tx(guardian3, guardian3_s4, guardian3_tx5)

# TODO should devices also post verifications?

@pytest.fixture(scope='module')
def verifier1_s1(verifier1_s0, static_transactions):
    return post_state(static_transactions, verifier1_s0, 'verifier', 1, 1)

@pytest.fixture(scope='module')
def verifier1_tx1(verifier1, static_transactions, static_files_dir):
    return post_tx(static_transactions, static_files_dir, verifier1, 1)

def test_verifier1_tx1(verifier1, verifier1_s0, verifier1_tx1):
    assert_tx(verifier1, verifier1_s0, verifier1_tx1)

@pytest.fixture(scope='module')
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
@pytest.fixture(scope='module')
def admin_tx7(
        admin: AdminNode,
        admin_tx6: Transaction,
        static_transactions, static_files_dir,
    ) -> Transaction:
    pairs = load_static_record_pairs(static_transactions['admin'][7][1], static_files_dir)
    tx = admin.post_public_records(
        new_record_pairs = pairs,
        new_phase = ElectionFinalizePhase(),
    )
    LOG.debug(f'admin_tx7: {tx}')
    admin.await_tx_confirmed(tx)
    return tx

def test_admin_tx7(admin, admin_s7, admin_tx7):
    assert_tx(admin, admin_s7, admin_tx7)

def test_phase6_verify(
        admin    , admin_s7    , admin_tx7,
        guardian1, guardian1_s5, guardian1_tx5,
        guardian2, guardian2_s5, guardian2_tx5,
        guardian3, guardian3_s5, guardian3_tx5,
        device1  , device1_s3  ,
        verifier1, verifier1_s1, verifier1_tx1,
    ):
    assert_nodes_converge([
        (admin    , admin_s7    ),
        (guardian1, guardian1_s5),
        (guardian2, guardian2_s5),
        (guardian3, guardian3_s5),
        (device1  , device1_s3  ),
        (verifier1, verifier1_s1),
    ], EgcPhase.FINALIZE)


## =================================
## 7. ElectionFinalizePhase:
##    - RmSubChannels
##    - EndElection
## =================================

@pytest.fixture(scope='module')
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

@pytest.fixture(scope='module')
def admin_tx8(
        admin: AdminNode,
        onboarding_info: dict[ChannelId, VerificationKeyHash],
        admin_tx7: Transaction,
        guardian1_tx5, guardian2_tx5, guardian3_tx5,
        device1_tx3, verifier1_tx1,
    ) -> Transaction:
    sub_ids = list(onboarding_info.keys())
    ch_strs = [channel_id_to_string(k) for k in sub_ids]
    tx = admin.rm_subchannels(subchannels = sub_ids)
    LOG.debug(f'admin_tx8: {tx}')
    admin.await_tx_confirmed(tx)
    return tx

def test_admin_tx8(admin, admin_s8, admin_tx8):
    assert_tx(admin, admin_s8, admin_tx8)

@pytest.fixture(scope='module')
def admin_tx9(
        admin: AdminNode,
        admin_tx8: Transaction,
    ) -> Transaction:
    tx = admin.end_election()
    LOG.debug(f'admin_tx9: {tx}')
    # this can't await_tx_confirmed, because last tx isn't indexed:
    admin.await_phase(EgcPhase.FINISHED)
    return tx

def test_admin_tx9(admin, admin_tx9):
    assert_tx(admin, None, admin_tx9)

def test_phase7_finalize(
        admin, admin_tx9,
        guardian1, guardian2, guardian3,
        device1, verifier1,
    ):
    assert_nodes_converge([
        (admin    , None),
        (guardian1, None),
        (guardian2, None),
        (guardian3, None),
        (device1  , None),
        (verifier1, None),
    ], EgcPhase.FINISHED)
