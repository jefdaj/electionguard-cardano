import json
import pytest

from os.path import realpath, join, exists
from pathlib import Path
from pycardano import OgmiosV6ChainContext, Address, SigningKey, VerificationKeyHash, UTxO
from typing import Dict, List

from election import ogmios as eo
from election import wallet as ew
from election import plutus as ep
from election.plutus import script as es

# TODO disambiguate from the module
@pytest.fixture(scope='session')
def ogmios() -> OgmiosV6ChainContext:
    '''Shared Ogmios connection for all testnet tests.'''
    return eo.OGMIOS_CTX

@pytest.fixture(scope='session')
def addr() -> Address:
    '''Load test publisher address.'''
    return ew.load_election_wallet_addr()

@pytest.fixture(scope='session')
def sk() -> SigningKey:
    '''Load test publisher signing key.'''
    return ew.load_election_wallet_signing_key()

@pytest.fixture(scope='session')
def vkh(sk: SigningKey) -> VerificationKeyHash:
    '''Load test publisher verification key hash.'''
    return ew.vkh_for_signing_key(sk)

# TODO explicit scope?
@pytest.fixture
def oneshot_utxo(ogmios: OgmiosV6ChainContext, addr: Address) -> UTxO:
    '''Pick a oneshot UTxO from the election wallet.'''
    return es.pick_oneshot_utxo(ogmios, addr)
