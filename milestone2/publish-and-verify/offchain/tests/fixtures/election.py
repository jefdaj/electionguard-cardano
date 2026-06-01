import logging

LOG = logging.getLogger(__name__)

@pytest.fixture(scope='package')
def oneshot_utxo(ogmios: OgmiosV6ChainContext, addr: Address) -> UTxO:
    '''Pick a oneshot UTxO from the election wallet.'''
    LOG.info('oneshot_utxo fixture')
    return eps.pick_oneshot_utxo(ogmios, addr)

@pytest.fixture(scope='package')
def script(oneshot_utxo: UTxO) -> eps.ElectionScript:
    '''Parameterize the contract with the oneshot_utxo.'''
    LOG.info('script fixture')
    return eps.ElectionScript(oneshot_utxo)

# TODO move? remove?
@pytest.fixture(scope='package')
def admin_channel_stt_assets(
        script: eps.ElectionScript,
        admin_id: ChannelId
    ) -> MultiAsset:
    LOG.info('admin_channel_stt_assets fixture')
    return erf.mint_channel_stt_assets(script.policy_id, 1, [admin_id])

# TODO package (election, scenario) scope Election object, which:
#      1. is a thin wrapper around helper fns from the init_and_burn scenario
#      2. yields the election, then checks if it finished and burns test tokens if needed
