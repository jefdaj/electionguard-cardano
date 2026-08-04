import pytest
from pycardano import *
from egc import *
import logging
import time

LOG = logging.getLogger(__name__)

@pytest.fixture(scope='module')
def admin(admin_wallet: Wallet, election_cfg: ElectionConfig, env2_tmp_root: Path) -> AdminNode:
    # TODO actual private dir?
    node_ = AdminNode(private_dir=env2_tmp_root, wallet=admin_wallet, election_cfg=election_cfg)
    LOG.debug(f'admin: {node_}')
    node_.await_phase(EgcPhase.CONFIG_ANNOUNCE)
    try:
        yield node_
        node_.return_collateral()
    finally:
        node_.stop()
