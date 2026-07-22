import pytest
from datetime import datetime
from pycardano import *
from egc import *
import logging
import time

LOG = logging.getLogger(__name__)


### dummy election context ###

# Mainly for testing serialization
@pytest.fixture(scope='module')
def dummy_deployment(
        ogmios: OgmiosV6ChainContext,
        funder_wallet: Wallet
    ) -> ElectionDeployment:
    tip = query_network_tip_sync()
    dd = ElectionDeployment(
        funder_address = str(funder_wallet.addr),
        since_slot     = tip['slot'],
        since_block    = tip['block_hash'],
        network_magic  = DEFAULT_NETWORK_MAGIC,
    )
    LOG.debug(f'dummy_deployment: {dd}')
    return dd

@pytest.fixture(scope='module')
def dummy_electioncontext(
        script: ElectionScript,
        dummy_deployment: ElectionDeployment,
    ) -> ElectionContext:
    dec = ElectionContext(script=script, deployment=dummy_deployment)
    LOG.debug(f'dummy_electioncontext: {dec}')
    return dec


### actual (on chain) election context ###
 
@pytest.fixture(scope='module')
def init_election_tuple(
        funder: ObserverNode,
        # script: ElectionScript,
        oneshot_utxo: UTxO,
        # admin_addr: Address,
        admin_vkh: VerificationKeyHash,
        keys_dir: Path,
        request, # exposes pytest info
    ) -> tuple[Transaction, ElectionConfig]:

    """Yields an already submitted and confirmed InitElection transaction, and
    the resulting ElectionContext. All other Transaction fixtures should depend
    on this one because it does the cleanup step (BurnTestTokens) if needed,
    tries to recover collateral, and logs total costs.
    """

    name = request.node.name
    ada_before = get_balance_ada(funder.publisher.wallet.addr)
    LOG.debug(f'funder balance before {name} is {ada_before} ADA.')

    # oneshot_hex = utxo_to_ref_hex(oneshot_utxo)

    (init_tx, cfg) = funder.init_election(
        # script     = script,
        oneshot_utxo = oneshot_utxo,
        # admin_addr = admin_addr,
        admin_vkh  = admin_vkh,
        admin_ada  = 200, # TODO what's a good amount?
    )
    funder.wait_for_confirmation(init_tx)

    # All other tests happen here
    yield (init_tx, cfg) # TODO config here, not context

    try:
        channel_ids = funder.subscriber.current_channel_ids()
        if len(channel_ids) == 0:
            LOG.debug('skip burn_tx because STTs already gone')
        else:
            # Can't use the node-level wait_for_confirmation here,
            # because the subscriber won't pick up the last TX.
            # TODO fix! should detect STT burn without output match/state.
            burn_tx = funder.burn_test_tokens()
            funder.publisher.wait_for_confirmation(burn_tx)

    except Exception as e:
        LOG.error(e, exc_info=True)
        # raise

    finally:
        last_tx = funder.recover_all_collateral(keys_dir)

        # Can't use the node-level wait_for_confirmation here,
        # because the subscriber won't pick up the unrelated TX.
        # TODO rename to make that requirement clearer?
        funder.publisher.wait_for_confirmation(last_tx)

        ada_after = get_balance_ada(funder.publisher.wallet.addr)
        LOG.debug(f'funder balance after {name} is {ada_after} ADA.')
        ada_diff = round(ada_before - ada_after, ndigits=2)
        if ada_diff > 50:
            fn = LOG.error
        else:
            fn = LOG.info
        fn(f'funder paid {ada_diff} ADA total to run {name}')

@pytest.fixture(scope='module')
def init_tx(init_election_tuple: tuple[Transaction, ElectionConfig]) -> Transaction:
    (tx, _) = init_election_tuple
    return tx

@pytest.fixture(scope='module')
def election_cfg(init_election_tuple: tuple[Transaction, ElectionConfig]) -> ElectionConfig:
    (_, cfg) = init_election_tuple
    return cfg

@pytest.fixture(scope='module')
def election_ctx(election_cfg: ElectionConfig):
    return ElectionContext.from_config(election_cfg)
