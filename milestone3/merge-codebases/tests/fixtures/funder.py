import pytest
from pycardano import *
from egc import *
from helpers import global_fixture, per_election_fixture
import logging

LOG = logging.getLogger(__name__)

@global_fixture
def funder_wallet() -> Wallet:
    w = Wallet.load_or_create(name='dev', verbose=False) # leave default, global keys_dir
    LOG.debug(f'funder_wallet: {w}')
    return w

@per_election_fixture
def funder_addr(funder_wallet: Wallet) -> Address:
    return funder_wallet.addr

@per_election_fixture
def funder(funder_wallet: Wallet) -> ObserverNode:
    node_ = ObserverNode(wallet=funder_wallet)
    LOG.debug(f'funder: {node_}')
    try:
        yield node_
        # no need to return collateral to self
    finally:
        node_.stop()

@per_election_fixture
def init_tx_builder(
        funder: ObserverNode,
        script: ElectionScript,
        admin_addr: Address,
        admin_vkh: VerificationKeyHash,
    ) -> TransactionBuilder:
    (_, txb) = funder._build_init_tx(
        script     = script,
        admin_addr = admin_addr,
        admin_vkh  = admin_vkh,
        admin_ada  = 10, # TODO what should this default to?
    )
    LOG.debug(f'init_txb: {txb}')
    return txb
