# Test order roughly matches onchain/tests/integration/happy_subchannel.ak

import pytest
from dataclasses import replace
from pycardano import *
from egc import *
# from data.static_records import *
from ..lib import *
from .lib import *
import logging
import time

LOG = logging.getLogger(__name__)


## ----------- setup for adding single subchannel -------------

@pytest.fixture(scope='module')
def s0(admin_vkh: VerificationKeyHash) -> ChannelState:
    return AdminChannel(state=AdminChannelState(
        admin       = admin_vkh.payload,
        ipfs_node   = NoIpfsNode(),
        subchannels = [],
        new_records = [],
        phase       = ElectionConfigPhase(ConfigAnnouncePhase()),
        seq         = 0,
    ))

@pytest.fixture(scope='module')
def tx0(init_tx: Transaction) -> Transaction:
    # tx0 is just the init_tx renamed for clarity.
    return init_tx

def test_tx0(admin, s0, tx0):
    assert_tx(admin, s0, tx0)

@pytest.fixture(scope='module')
def s1(
        s0: ChannelState,
        static_transactions, static_files_dir,
        static_phases,
    ) -> ChannelState:
    prev = s0.state
    record_pairs = load_static_record_pairs(
        static_transactions['admin'][1][1], static_files_dir,
    )
    return AdminChannel(state=replace(
        prev,
        new_records = record_pairs,
        phase       = static_phases[1],
        seq         = 1,
    ))

@pytest.fixture(scope='module')
def tx1(
        tx0: Transaction,
        admin: AdminNode,
        static_transactions, static_files_dir,
        static_phases,
    ) -> Transaction:
    record_pairs = load_static_record_pairs(
        static_transactions['admin'][1][1], static_files_dir,
    )
    tx = admin.post_public_records(
        new_record_pairs = record_pairs,
        new_phase = static_phases[1],
    )
    LOG.debug(f'tx1: {tx}')
    admin.await_tx_confirmed(tx)
    return tx

def test_tx1(admin, s1, tx1):
    assert_tx(admin, s1, tx1)


## -------- tx2: add single subchannel --------

@pytest.fixture(scope='module')
def onboarding_info(
        guardian1: GuardianNode,
    ) -> dict[ChannelId, VerificationKeyHash]:
    info = {
        guardian1.channel_id() : guardian1.publisher.wallet.vkh
    }
    return info

@pytest.fixture(scope='module')
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

@pytest.fixture(scope='module')
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
        done_onboarding = True, # advance to ceremony phase
    )
    LOG.debug(f'tx2: {tx}')
    admin.await_tx_confirmed(tx)
    return tx

def test_add_subchannel(
        admin, s2, tx2,
        guardian1, guardian1_s0,
    ):
    assert_tx(admin, s2, tx2)
    assert_nodes_converge([
        (admin, s2),
        (guardian1, guardian1_s0),
    ], EgcPhase.CONFIG_CEREMONY)


## ----------- tx3: rm single subchannel -----------

@pytest.fixture(scope='module')
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

@pytest.fixture(scope='module')
def tx3(
        tx2: Transaction,
        admin: AdminNode,
        onboarding_info: dict[ChannelId, VerificationKeyHash],
    ) -> Transaction:
    sub_ids = list(onboarding_info.keys())
    ch_strs = [channel_id_to_string(k) for k in sub_ids]
    tx = admin.rm_subchannels(subchannels = sub_ids)
    LOG.debug(f'tx3: {tx}')
    admin.await_tx_confirmed(tx)
    return tx

def test_rm_subchannel(admin, s3, tx3, guardian1):
    assert_tx(admin, s3, tx3)
    assert_nodes_converge([
        (admin, s3),
        (guardian1, None)
    ], EgcPhase.CONFIG_CEREMONY)
