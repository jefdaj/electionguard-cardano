# Test order roughly matches onchain/tests/integration/happy_election.ak

import pytest
from dataclasses import replace
from pycardano import *
from egc import *
from helpers import per_election_fixture, assert_nodes_in_sync
import logging
import time

LOG = logging.getLogger(__name__)


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

@pytest.mark.testnet
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
@pytest.mark.testnet
def test_admin_tx0_sub(
        funder: FunderNode,
        admin: AdminNode,
        admin_tx0: Transaction,
    ):
    nodes = [funder, admin]
    assert_nodes_in_sync(nodes)


## ----------- admin_tx1 -----------

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
        static_phases,
    ) -> Transaction:
    tx = admin.post_public_records(
        new_records = static_transactions['admin'][1][1],
        new_phase   = static_phases[1],
    )
    LOG.debug(f'admin_tx1: {tx}')
    admin.wait_for_confirmation(tx)
    return tx

@pytest.mark.testnet
def test_admin_tx1(
        admin: AdminNode,
        admin_s1: ChannelState,
        admin_tx1: Transaction,
    ):
    assert isinstance(admin_tx1, Transaction)
    actual_state = admin.subscriber.states[ADMIN_CHANNEL_ID][1]
    assert actual_state == admin_s1

@pytest.mark.testnet
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

@pytest.mark.local
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
        subchannel_ids,
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
    return {k:v for (k,v) in zip(subchannel_ids, wallets)} # TODO sort?

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

@pytest.mark.testnet
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

@pytest.mark.testnet
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
    ):
    assert isinstance(admin_tx3, Transaction)
    actual_state = admin.subscriber.states[ADMIN_CHANNEL_ID][1]
    assert actual_state == admin_s3

@pytest.mark.testnet
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
    ):
    assert isinstance(admin_tx4, Transaction)
    actual_state = admin.subscriber.states[ADMIN_CHANNEL_ID][1]
    assert actual_state == admin_s4

@pytest.mark.testnet
def test_admin_tx4_sub(
        admin_tx4: Transaction,
        all_nodes: list[ElectionNode],
    ):
    assert_nodes_in_sync(all_nodes)


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
    ):
    assert isinstance(admin_tx5, Transaction)
    actual_state = admin.subscriber.states[ADMIN_CHANNEL_ID][1]
    assert actual_state == admin_s5

@pytest.mark.testnet
def test_admin_tx5_sub(
        admin_tx5: Transaction,
        all_nodes: list[ElectionNode],
    ):
    assert_nodes_in_sync(all_nodes)


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
    ):
    assert isinstance(admin_tx6, Transaction)
    actual_state = admin.subscriber.states[ADMIN_CHANNEL_ID][1]
    assert actual_state == admin_s6

@pytest.mark.testnet
def test_admin_tx6_sub(
        admin_tx6: Transaction,
        all_nodes: list[ElectionNode],
    ):
    assert_nodes_in_sync(all_nodes)



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
    ):
    assert isinstance(admin_tx7, Transaction)
    actual_state = admin.subscriber.states[ADMIN_CHANNEL_ID][1]
    assert actual_state == admin_s7

@pytest.mark.testnet
def test_admin_tx7_sub(
        admin_tx7: Transaction,
        all_nodes: list[ElectionNode],
    ):
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

# TODO move to helpers and use everywhere?
# TODO rename _sub tests -> checkpoints and add cross-channel dependencies
def assert_node_state(
        node: ElectionNode,
        expected_state: ChannelState,
    ):
    assert isinstance(node, ElectionNode)
    assert isinstance(expected_state, ChannelState)
    node_str = node.channel_str()
    (state_utxo, actual_state) = node.state()
    LOG.debug(f'{node_str} latest state utxo: {state_utxo}')
    LOG.debug(f'{node_str} state as expected: {actual_state}')
    assert actual_state == expected_state

@pytest.mark.testnet
def test_admin_tx8(
        admin: AdminNode,
        admin_s8: ChannelState,
        admin_tx8: Transaction,
    ):
    assert isinstance(admin_tx8, Transaction)
    # actual_state = admin.subscriber.states[ADMIN_CHANNEL_ID][1]
    # assert actual_state == admin_s8
    assert_node_state(admin, admin_s8)

# @pytest.mark.testnet
# def test_admin_tx8_sub(
#         admin_tx8: Transaction,
#         all_nodes: list[ElectionNode],
#     ):
#     assert_nodes_in_sync(all_nodes)
