import pytest
from pycardano import *
from egc import *
import logging
import time
from ..lib import fixture_private_dir

LOG = logging.getLogger(__name__)

@pytest.fixture(scope='module')
def admin(admin_wallet: Wallet, election_cfg: ElectionConfig, env2_tmp_root: Path, request) -> AdminNode:
    # TODO actual private dir?
    node_ = AdminNode(
        private_dir  = fixture_private_dir(env2_tmp_root, request),
        wallet       = admin_wallet,
        election_cfg = election_cfg
    )
    LOG.debug(f'admin: {node_}')
    node_.ipfs.wait_until_stable_sync()
    node_.await_phase(EgcPhase.CONFIG_ANNOUNCE)
    try:
        yield node_
        node_.return_collateral()
    finally:
        node_.stop()
