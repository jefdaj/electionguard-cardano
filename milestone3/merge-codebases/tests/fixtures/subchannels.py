import pytest
from pycardano import *
from egc import *
from helpers import per_election_fixture, sub_s0
import logging

LOG = logging.getLogger(__name__)


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


## ------- subchannel nodes --------

@per_election_fixture
def guardian1(
        election_cfg: ElectionConfig,
        guardian1_wallet: Wallet,
    ) -> GuardianNode:
    node_ = GuardianNode(
        election_cfg = election_cfg,
        wallet     = guardian1_wallet,
        role_index = 1,
    )
    LOG.debug(f'guardian1: {node_}')
    try:
        yield node_
        node_.return_collateral()
    finally:
        node_.stop()

@per_election_fixture
def guardian2(
        election_cfg: ElectionConfig,
        guardian2_wallet: Wallet,
    ) -> GuardianNode:
    node_ = GuardianNode(
        election_cfg = election_cfg,
        wallet     = guardian2_wallet,
        role_index = 2,
    )
    LOG.debug(f'guardian2: {node_}')
    try:
        yield node_
        node_.return_collateral()
    finally:
        node_.stop()

@per_election_fixture
def guardian3(
        election_cfg: ElectionConfig,
        guardian3_wallet: Wallet,
    ) -> GuardianNode:
    node_ = GuardianNode(
        election_cfg = election_cfg,
        wallet     = guardian3_wallet,
        role_index = 3,
    )
    LOG.debug(f'guardian3: {node_}')
    try:
        yield node_
        node_.return_collateral()
    finally:
        node_.stop()

@per_election_fixture
def device1(
        election_cfg: ElectionConfig,
        device1_wallet: Wallet,
    ) -> DeviceNode:
    node_ = DeviceNode(
        election_cfg = election_cfg,
        wallet     = device1_wallet,
        role_index = 1,
    )
    LOG.debug(f'device1: {node_}')
    try:
        yield node_
        node_.return_collateral()
    finally:
        node_.stop()

@per_election_fixture
def verifier1(
        election_cfg: ElectionConfig,
        verifier1_wallet: Wallet,
    ) -> VerifierNode:
    node_ = VerifierNode(
        election_cfg = election_cfg,
        wallet     = verifier1_wallet,
        role_index = 1,
    )
    LOG.debug(f'verifier1: {node_}')
    try:
        yield node_
        node_.return_collateral()
    finally:
        node_.stop()

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


## ------- subchannel initial states --------

@per_election_fixture
def guardian1_s0(guardian1: GuardianNode) -> ChannelState:
    return sub_s0(guardian1.channel_id(), guardian1.publisher.wallet.vkh)

@per_election_fixture
def guardian2_s0(guardian2: GuardianNode) -> ChannelState:
    return sub_s0(guardian2.channel_id(), guardian2.publisher.wallet.vkh)

@per_election_fixture
def guardian3_s0(guardian3: GuardianNode) -> ChannelState:
    return sub_s0(guardian3.channel_id(), guardian3.publisher.wallet.vkh)

@per_election_fixture
def device1_s0(device1: DeviceNode) -> ChannelState:
    return sub_s0(device1.channel_id(), device1.publisher.wallet.vkh)

@per_election_fixture
def verifier1_s0(verifier1: VerifierNode) -> ChannelState:
    return sub_s0(verifier1.channel_id(), verifier1.publisher.wallet.vkh)
