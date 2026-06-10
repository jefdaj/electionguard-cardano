# Test order roughly matches onchain/tests/integration/happy_election.ak

import pytest
from dataclasses import replace
from pycardano import *
from egc import *
from test_utils import per_election_fixture, assert_nodes_in_sync
from static_records import STATIC_PHASES, STATIC_TRANSACTIONS
import logging
import time

LOG = logging.getLogger(__name__)

SUBCHANNEL_IDS = STATIC_TRANSACTIONS['admin'][2][0].channels
[G1, G2, G3, D1, V1] = SUBCHANNEL_IDS


## =================================
## initial solo admin transactions:
## 0. init election
## 1. announce config
## 2. onboarding (add subchannels)
##    - subchannel wallets
##    - subchannel nodes
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
    nodes = [funder, admin]
    assert_nodes_in_sync(nodes)


## ----------- admin_tx1 -----------

@per_election_fixture
def admin_s1(admin_s0: ChannelState) -> ChannelState:
    prev = admin_s0.state
    return AdminChannel(state=replace(
        prev,
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
    admin.wait_for_confirmation(tx)
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
    nodes = [funder, admin]
    assert_nodes_in_sync(nodes)


## ------ subchannel wallets -------

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


## ------- subchannel nodes --------

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

@per_election_fixture
def guardian2(
        election: ElectionContext,
        guardian2_wallet: Wallet
    ) -> GuardianNode:
    node = GuardianNode(
        election   = election,
        wallet     = guardian2_wallet,
        role_index = 2,
    )
    LOG.debug(f'guardian2: {node}')
    try:
        yield node
    finally:
        node.stop()

@per_election_fixture
def guardian3(
        election: ElectionContext,
        guardian3_wallet: Wallet
    ) -> GuardianNode:
    node = GuardianNode(
        election   = election,
        wallet     = guardian3_wallet,
        role_index = 3,
    )
    LOG.debug(f'guardian3: {node}')
    try:
        yield node
    finally:
        node.stop()

@per_election_fixture
def device1(
        election: ElectionContext,
        device1_wallet: Wallet
    ) -> DeviceNode:
    node = DeviceNode(
        election   = election,
        wallet     = device1_wallet,
        role_index = 1,
    )
    LOG.debug(f'device1: {node}')
    try:
        yield node
    finally:
        node.stop()

@per_election_fixture
def verifier1(
        election: ElectionContext,
        verifier1_wallet: Wallet
    ) -> VerifierNode:
    node = VerifierNode(
        election   = election,
        wallet     = verifier1_wallet,
        role_index = 1,
    )
    LOG.debug(f'verifier1: {node}')
    try:
        yield node
    finally:
        node.stop()

@per_election_fixture
def subchannel_nodes(
        guardian1: GuardianNode,
        guardian2: GuardianNode,
        guardian3: GuardianNode,
        device1: DeviceNode,
        verifier1: VerifierNode,
    ) -> list[ElectionNode]:
    return [
        guardian1,
        guardian2,
        guardian3,
        device1,
        verifier1,
    ]

# from here on all the nodes can be started and should stay in sync
@per_election_fixture
def all_nodes(
        funder: FunderNode,
        admin: AdminNode,
        subchannel_nodes: list[ElectionNode],
    ) -> list[ElectionNode]:
    return [funder, admin] + subchannel_nodes


## ----------- admin_tx2 -----------

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
        subchannel_nodes: list[ElectionNode],
    ) -> dict[ChannelId, VerificationKeyHash]:
    info = {
        node.channel_id() : node.publisher.wallet.vkh
        for node in subchannel_nodes
    }
    ch_strs = [ChannelIdHelper.to_string(k) for k in info.keys()]
    LOG.info(f'Gathered subchannel onboarding info from {', '.join(ch_strs)}')
    return info

@per_election_fixture
def admin_s2(admin_s1: ChannelState) -> ChannelState:
    prev = admin_s1.state
    return AdminChannel(state=replace(
        prev,
        subchannels = SUBCHANNEL_IDS,
        new_records = [],
        phase       = STATIC_PHASES[2],
        seq         = 2,
    ))

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
    admin.wait_for_confirmation(tx)
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
        all_nodes: list[ElectionNode],
    ):
    assert_nodes_in_sync(all_nodes)


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
def admin_s3(admin_s2: ChannelState) -> ChannelState:
    prev = admin_s2.state
    return AdminChannel(state=replace(
        prev,
        new_records = STATIC_TRANSACTIONS['admin'][3][1],
        phase       = STATIC_PHASES[3],
        seq         = 3,
    ))

@per_election_fixture
def admin_tx3(
        admin: AdminNode,
        admin_tx2: Transaction,
    ) -> Transaction:
    tx = admin.post_public_records(
        new_records = STATIC_TRANSACTIONS['admin'][3][1],
        new_phase   = STATIC_PHASES[3],
    )
    LOG.debug(f'admin_tx3: {tx}')
    admin.wait_for_confirmation(tx)
    return tx

def test_admin_tx3(
        admin: AdminNode,
        admin_s3: ChannelState,
        admin_tx3: Transaction,
    ):
    assert isinstance(admin_tx3, Transaction)
    actual_state = admin.subscriber.states[ADMIN_CHANNEL_ID][1]
    assert actual_state == admin_s3

def test_admin_tx3_sub(
        admin_tx3: Transaction,
        all_nodes: list[ElectionNode],
    ):
    assert_nodes_in_sync(all_nodes)


## ----------- admin_tx4 -----------

# This could be combined with posting the tally, but in later versions I think
# it would make more sense to have this be a definite stopping point where
# devices post any last votes and their STTs are burned (channels removed). So
# for now I'll keep it as an advance-only step.

@per_election_fixture
def admin_s4(admin_s3: ChannelState) -> ChannelState:
    prev = admin_s3.state
    return AdminChannel(state=replace(
        prev,
        new_records = [],
        phase       = STATIC_PHASES[4],
        seq         = 4,
    ))

@per_election_fixture
def admin_tx4(
        admin: AdminNode,
        admin_tx3: Transaction,
    ) -> Transaction:
    tx = admin.advance_phase(STATIC_PHASES[4])
    LOG.debug(f'admin_tx4: {tx}')
    admin.wait_for_confirmation(tx)
    return tx

def test_admin_tx4(
        admin: AdminNode,
        admin_s4: ChannelState,
        admin_tx4: Transaction,
    ):
    assert isinstance(admin_tx4, Transaction)
    actual_state = admin.subscriber.states[ADMIN_CHANNEL_ID][1]
    assert actual_state == admin_s4

def test_admin_tx4_sub(
        admin_tx4: Transaction,
        all_nodes: list[ElectionNode],
    ):
    assert_nodes_in_sync(all_nodes)


## ----------- admin_tx5 -----------

@per_election_fixture
def admin_s5(admin_s4: ChannelState) -> ChannelState:
    prev = admin_s4.state
    return AdminChannel(state=replace(
        prev,
        new_records = STATIC_TRANSACTIONS['admin'][5][1],
        phase       = STATIC_PHASES[5],
        seq         = 5,
    ))

@per_election_fixture
def admin_tx5(
        admin: AdminNode,
        admin_tx4: Transaction,
    ) -> Transaction:
    tx = admin.post_public_records(
        new_records = STATIC_TRANSACTIONS['admin'][5][1],
        new_phase   = STATIC_PHASES[5],
    )
    LOG.debug(f'admin_tx5: {tx}')
    admin.wait_for_confirmation(tx)
    return tx

def test_admin_tx5(
        admin: AdminNode,
        admin_s5: ChannelState,
        admin_tx5: Transaction,
    ):
    assert isinstance(admin_tx5, Transaction)
    actual_state = admin.subscriber.states[ADMIN_CHANNEL_ID][1]
    assert actual_state == admin_s5

def test_admin_tx5_sub(
        admin_tx5: Transaction,
        all_nodes: list[ElectionNode],
    ):
    assert_nodes_in_sync(all_nodes)


## ----------- admin_tx6 -----------

@per_election_fixture
def admin_s6(admin_s5: ChannelState) -> ChannelState:
    prev = admin_s5.state
    return AdminChannel(state=replace(
        prev,
        new_records = STATIC_TRANSACTIONS['admin'][6][1],
        phase       = STATIC_PHASES[6],
        seq         = 6,
    ))

@per_election_fixture
def admin_tx6(
        admin: AdminNode,
        admin_tx5: Transaction,
    ) -> Transaction:
    tx = admin.post_public_records(
        new_records = STATIC_TRANSACTIONS['admin'][6][1],
        new_phase   = STATIC_PHASES[6],
    )
    LOG.debug(f'admin_tx6: {tx}')
    admin.wait_for_confirmation(tx)
    return tx

def test_admin_tx6(
        admin: AdminNode,
        admin_s6: ChannelState,
        admin_tx6: Transaction,
    ):
    assert isinstance(admin_tx6, Transaction)
    actual_state = admin.subscriber.states[ADMIN_CHANNEL_ID][1]
    assert actual_state == admin_s6

def test_admin_tx6_sub(
        admin_tx6: Transaction,
        all_nodes: list[ElectionNode],
    ):
    assert_nodes_in_sync(all_nodes)



## ----------- admin_tx7 -----------

@per_election_fixture
def admin_s7(admin_s6: ChannelState) -> ChannelState:
    prev = admin_s6.state
    return AdminChannel(state=replace(
        prev,
        new_records = STATIC_TRANSACTIONS['admin'][7][1],
        phase       = STATIC_PHASES[7],
        seq         = 7,
    ))

@per_election_fixture
def admin_tx7(
        admin: AdminNode,
        admin_tx6: Transaction,
    ) -> Transaction:
    tx = admin.post_public_records(
        new_records = STATIC_TRANSACTIONS['admin'][7][1],
        new_phase   = STATIC_PHASES[7],
    )
    LOG.debug(f'admin_tx7: {tx}')
    admin.wait_for_confirmation(tx)
    return tx

def test_admin_tx7(
        admin: AdminNode,
        admin_s7: ChannelState,
        admin_tx7: Transaction,
    ):
    assert isinstance(admin_tx7, Transaction)
    actual_state = admin.subscriber.states[ADMIN_CHANNEL_ID][1]
    assert actual_state == admin_s7

def test_admin_tx7_sub(
        admin_tx7: Transaction,
        all_nodes: list[ElectionNode],
    ):
    assert_nodes_in_sync(all_nodes)


