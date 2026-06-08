import pytest
from pycardano import *
from egc import *
from test_utils import global_fixture, per_election_fixture
import logging

LOG = logging.getLogger(__name__)

@global_fixture
def funder_wallet() -> Wallet:
    kp = Wallet.load_or_create(name='dev', verbose=False) # leave default, global keys_dir
    LOG.info(f'funder_wallet: {kp}')
    return kp

@per_election_fixture
def funder_addr(funder_wallet: Wallet) -> Address:
    return funder_wallet.addr

@per_election_fixture
def funder(funder_wallet: Wallet) -> FunderNode:
    node = FunderNode(wallet=funder_wallet)
    LOG.info(f'funder: {node}')
    try:
        yield node
    finally:
        if node.subscriber is not None:
            node.subscriber.stop()

@per_election_fixture
def init_tx_builder(
        funder: FunderNode,
        script: ElectionScript,
        admin_addr: Address,
        admin_vkh: VerificationKeyHash,
    ) -> TransactionBuilder:
    txb = funder._build_init_tx(
        script     = script,
        admin_addr = admin_addr,
        admin_vkh  = admin_vkh,
        admin_ada  = 10, # TODO what should this default to?
    )
    LOG.info(f'init_txb: {txb}')
    return txb
