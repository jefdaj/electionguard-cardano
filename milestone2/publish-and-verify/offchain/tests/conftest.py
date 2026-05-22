import json
import pytest

from os.path import realpath, join, exists
from pathlib import Path
from pycardano import OgmiosV6ChainContext, Address, SigningKey, VerificationKeyHash, UTxO, MultiAsset
from typing import Dict, List

from election import ogmios as eo
from election import wallet as ew
from election import plutus as ep
from election.plutus import script as eps
from election.plutus.types.channel_id import *
from election.roles import funder as erf
import logging

log = logging.getLogger(__name__)

# TODO disambiguate from the module
@pytest.fixture(scope='session')
def ogmios() -> OgmiosV6ChainContext:
    '''Shared Ogmios connection for all testnet tests.'''
    log.info('ogmios fixture')
    return eo.OGMIOS_CTX

@pytest.fixture(scope='session')
def addr() -> Address:
    '''Load test publisher address.'''
    log.info('addr fixture')
    return ew.load_wallet_addr()

@pytest.fixture(scope='session')
def sk() -> SigningKey:
    '''Load test publisher signing key.'''
    log.info('sk fixture')
    return ew.load_wallet_signing_key()

@pytest.fixture(scope='session')
def vkh(sk: SigningKey) -> VerificationKeyHash:
    '''Load test publisher verification key hash.'''
    log.info('vkh fixture')
    return ew.vkh_for_signing_key(sk)

# TODO do we ever want this one to persist between tests?
@pytest.fixture(scope='module')
def oneshot_utxo(ogmios: OgmiosV6ChainContext, addr: Address) -> UTxO:
    '''Pick a oneshot UTxO from the election wallet.'''
    log.info('oneshot_utxo fixture')
    return eps.pick_oneshot_utxo(ogmios, addr)

@pytest.fixture(scope='module')
def script(oneshot_utxo: UTxO) -> eps.ElectionScript:
    '''Parameterize the contract with the oneshot_utxo.'''
    log.info('script fixture')
    return eps.ElectionScript(oneshot_utxo)

@pytest.fixture(scope='module')
def admin_id() -> ChannelId:
    log.info('admin_id fixture')
    return ChannelIdHelper.from_string('admin')

@pytest.fixture(scope='module')
def subchannel_ids() -> List[ChannelId]:
    log.info('subchannel_ids fixture')
    strs = ['guardian1', 'guardian2', 'guardian3', 'device1', 'verifier1']
    return [ChannelIdHelper.from_string(s) for s in strs]

@pytest.fixture(scope='module')
def admin_channel_stt_assets(
        script: eps.ElectionScript,
        admin_id: ChannelId
    ) -> MultiAsset:
    log.info('admin_channel_stt_assets fixture')
    return erf.mint_channel_stt_assets(script.policy_id, 1, [admin_id])

@pytest.fixture(scope='module')
def subchannel_stt_assets(
        script: eps.ElectionScript,
        subchannel_ids: List[ChannelId]
    ) -> MultiAsset:
    log.info('subchannel_stt_assets fixture')
    return erf.mint_channel_stt_assets(script.policy_id, 1, subchannel_ids)


