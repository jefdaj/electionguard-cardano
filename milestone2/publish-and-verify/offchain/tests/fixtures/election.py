import pytest
from datetime import datetime
from pycardano import *
from egc import *
from test_utils import per_election_fixture
import logging
import time

LOG = logging.getLogger(__name__)


### dummy election context ###

# Mainly for testing serialization
@per_election_fixture
def dummy_deployment(
        ogmios: OgmiosV6ChainContext,
        funder_wallet: Wallet
    ) -> ElectionDeployment:
    tip = query_network_tip_sync()
    dd = ElectionDeployment(
        network               = Network.TESTNET,
        funder_address        = funder_wallet.addr,
        deployment_date       = datetime.now(),
        index_from_slot       = tip['slot'],
        index_from_block_hash = tip['block_hash'],
    )
    LOG.debug(f'dummy_deployment: {dd}')
    return dd

@per_election_fixture
def dummy_electioncontext(
        script: ElectionScript,
        dummy_deployment: ElectionDeployment,
    ) -> ElectionContext:
    dec = ElectionContext(script=script, deployment=dummy_deployment)
    LOG.debug(f'dummy_electioncontext: {dec}')
    return dec


### actual (on chain) election context ###
 
@per_election_fixture
def election(init_tx: Transaction, funder: FunderNode) -> ElectionContext:
    # init_tx ensures that this exists, and cleans up after it:
    ctx = funder.election
    LOG.debug(f'ctx: {ctx}')
    return ctx

@per_election_fixture
def init_tx(
        funder: FunderNode,
        script: ElectionScript,
        admin_addr: Address,
        admin_vkh: VerificationKeyHash,
        keys_dir: Path,
    ) -> Transaction:
    """Yields an already submitted and confirmed InitElection transaction.
    For now, all other Transaction fixtures should depend on this one,
    because it does the cleanup step (BurnTestTokens) if needed.
    Also tries to recover all possible collateral during cleanup.
    """

    init_tx = funder.init_election(
        script     = script,
        admin_addr = admin_addr,
        admin_vkh  = admin_vkh,
        admin_ada  = 10, # TODO what's a good amount?
    )
    funder.publisher.wait_for_confirmation(init_tx)

    time.sleep(KUPO_DELAY_SEC) # TODO remove?

    # All other tests happen here
    yield init_tx

    try:
        time.sleep(KUPO_DELAY_SEC) # TODO remove?
        burn_tx = funder.burn_test_tokens()
        funder.publisher.wait_for_confirmation(burn_tx)

    except Exception as e:
        LOG.error(e)
        raise

    finally:
        time.sleep(KUPO_DELAY_SEC) # TODO remove?
        funder.sweep_all_collateral(keys_dir)
