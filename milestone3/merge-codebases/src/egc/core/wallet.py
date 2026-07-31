"""Generate and manage wallets with a focus on testing.

Expects that there will be one main dev wallet with a supply of (t)ADA,
and then lots of temporary test wallets.

When EGC_MODE=test, it will:

- leave of generated keys in the tmpdir (normally /tmp/nix-shell.XXXXX)
- log signing keys to <keys_dir>/wallets.log
"""

from __future__ import annotations

import json
import qrcode
from pathlib import Path
from typing import Optional, Self, Tuple
from dataclasses import dataclass
from pycardano import *
from .env import EGC_WALLET_MODE, EGC_WALLET_DIR
import logging
import shutil


# Regular logger
LOG = logging.getLogger(__name__)

# Separate logger for test keys
KEYS_LOG = logging.getLogger('test-wallets')
if EGC_WALLET_MODE == 'scripted':
    log_path = (EGC_WALLET_DIR / 'wallets.log').absolute()
    keys_fh = logging.FileHandler(log_path)
    keys_fh.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    KEYS_LOG.addHandler(keys_fh)
    KEYS_LOG.setLevel(logging.DEBUG)
    # TODO why isn't this logged during pytest?
    del keys_fh
    del log_path
else:
    KEYS_LOG.setLevel(logging.CRITICAL + 1)
    KEYS_LOG.propagate = False
    KEYS_LOG.critical('IF YOU CAN READ THIS, YOU MAY BE LEAKING PRODUCTION KEYS!')


@dataclass(frozen=True, slots=True)
class Wallet:
    """A convenience bundle around a Cardano `SigningKey`.

    Everything except `sk` is derived, so equality, serialization, and
    persistence are all driven by the signing key alone.
    """

    # TODO parse desc, and write it back, and remove wallet_name from server state
    sk:   SigningKey # holds the wallet name (TODO desc?) as its description field
    vk:   VerificationKey
    vkh:  VerificationKeyHash
    addr: Address

    @classmethod
    def from_signing_key(cls, sk: SigningKey) -> Self:
        LOG.debug('Wallet.from_signing_key')
        vk = vk_for_signing_key(sk)
        return cls(
            sk=sk,
            vk=vk,
            vkh=vk.hash(),
            addr=addr_for_signing_key(sk),
        )

    @classmethod
    def from_json(cls, data: str) -> Self:
        return cls.from_signing_key(SigningKey.from_json(data))

    @classmethod
    def from_qr_str(cls, txt: str) -> Self:
        "egc:wallet:<desc>:<type>:<cborhex>, maybe with wrapping"
        txt = ''.join(l.strip() for l in txt.splitlines())
        words = txt.split(':')
        prefix = words[:2]
        args   = words[2:]
        assert prefix == ['egc', 'wallet']
        assert len(args) == 3
        desc, type_, cbor_hex = args
        assert type_ == "PaymentSigningKeyShelley_ed25519"
        sk_dict = {
              "type": type_,
              "description": desc,
              "cborHex": cbor_hex,
        }
        return cls.from_json(sk_dict)

    def to_qr_str(self) -> str:
        "egc:wallet:<desc>:<type>:<cborhex>"
        sk_dict = json.loads(self.sk.to_json())
        qr_txt = ':'.join([
            'egc', 'wallet',
            sk_dict['description'].replace(':', ';'), # escape colons
            sk_dict['type'],
            sk_dict['cborHex'],
        ])
        return qr_txt

    @classmethod
    def from_sk_path(cls, sk_path: Path) -> Self:
        LOG.debug('Wallet.from_sk_path: %s', sk_path)
        return cls.from_json(Path(sk_path).read_text())

    @classmethod
    def load_or_create(
        cls,
        keys_dir: Path = EGC_WALLET_DIR,
        name: str = 'wallet',
        description: str = 'Generated EGC wallet', # TODO no default?
        verbose: bool = True,
    ) -> Self:
        """Load the wallet named `name` from `keys_dir`, generating it if absent."""
        keys_dir = Path(keys_dir)
        sk_path = keys_dir / f'{name}.sk'

        if sk_path.exists():
            LOG.debug('sk_path exists; loading: %s', sk_path)
            return load_wallet(sk_path)

        return create_wallet(
            keys_dir    = keys_dir,
            name        = name,
            description = description,
            verbose     = verbose
        )

    def to_json(self, *args, **kwargs) -> str:
        return self.sk.to_json(*args, **kwargs)

    def save(self, sk_path: Path) -> None:
        sk_path = Path(sk_path)
        sk_path.absolute().parent.mkdir(parents=True, exist_ok=True)
        sk_path.write_text(self.to_json())

    # TODO __str__ here?
    def __repr__(self) -> str:
        return f'Wallet(addr={self.addr!r}, vkh={self.vkh.to_cbor_hex()[:12]}…)'


def vk_for_signing_key(sk: PaymentSigningKey) -> VerificationKey:
    verification_key = PaymentVerificationKey.from_signing_key(sk)
    return verification_key

def addr_for_signing_key(sk: PaymentSigningKey) -> Address:
    vk = PaymentVerificationKey.from_signing_key(sk)
    return addr_for_vkh(vk.hash())

def addr_for_vkh(vkh: VerificationKeyHash) -> Address:
    return Address(payment_part=vkh, network=Network.TESTNET)

def load_wallet(sk_path: Optional[Path] = None, keys_dir=EGC_WALLET_DIR, name='default') -> Wallet:
    LOG.debug('load_wallet')
    if sk_path is None:
        keys_dir = Path(keys_dir)
        sk_path = keys_dir / f'{name}.sk'
    return Wallet.from_sk_path(sk_path)

def load_wallet_by_address(address: Address, keys_dir=EGC_WALLET_DIR) -> Optional[Tuple[Path, Wallet]]:
    "Mainly to help return collateral in test fixtures."
    LOG.debug('load_wallet_for_address')
    keys_dir = Path(keys_dir)
    for sk_path in sorted(keys_dir.glob('*.sk')):
        w = Wallet.from_sk_path(sk_path)
        if w.addr == address:
            return (sk_path, w)
    return None

def set_sk_description(sk: PaymentSigningKey, desc: str) -> PaymentSigningKey:
    # roundabout way to set description, which doesn't have a setter
    sk_dict = json.loads(sk.to_json())
    sk_dict['description'] = desc
    sk = PaymentSigningKey.from_json(json.dumps(sk_dict))
    return sk

def create_wallet(keys_dir=EGC_WALLET_DIR, name='wallet', description='Generated EGC wallet', verbose=True, overwrite=False) -> Wallet:
    LOG.debug('create_wallet')
    if EGC_WALLET_MODE == 'scripted':
        log_path = (EGC_WALLET_DIR / 'wallets.log').absolute()
        LOG.warning(f'Running in test mode, so all keys will be logged to {log_path}')
    keys_dir = Path(keys_dir)
    sk_path  = keys_dir / f'{name}.sk'
    if sk_path.exists() and not overwrite:
        err = f'ERROR: sk_path already exists: {sk_path}'
        LOG.error(err)
        raise Exception(err)
    if overwrite:
        shutil.rmtree(sk_path, ignore_errors=True)
    keys_dir.mkdir(parents=True, exist_ok=True)
    signing_key = PaymentSigningKey.generate()
    signing_key = set_sk_description(signing_key, description)
    # this has issues with existing files, and description not setting:
    # signing_key.save(str(sk_path))
    # so we save it manually instead:
    sk_path.write_text(signing_key.to_json())
    LOG.info(f'Generated {sk_path}')
    # round-trip to make sure it was saved properly before using:
    wallet = Wallet.from_sk_path(sk_path)
    msg = f'''
    Your new Preview testnet key \"{name} ({description})\" is here:

    {sk_path}

    You can load it in Python like this:

    wallet = Wallet.from_sk_path("{sk_path}")

    Its public address is: {wallet.addr}

    If this is your main dev wallet, go fund that address with tADA from the
    faucet before running any tests:
    https://docs.cardano.org/cardano-testnets/tools/faucet

    If you don't, local tests will still work but testnet tests will fail.
    '''
    LOG.debug(msg)
    if verbose:
        print(msg)
    KEYS_LOG.debug(
        'Created Wallet:\n\n'
        '  name = %s\n'
        '  desc = %s\n'
        '  addr = %s\n'
        '  vkh  = %s\n'
        '  vk   = %s\n'
        '  sk   = %s\n',
        name,
        wallet.sk.description,
        wallet.addr,
        wallet.vkh.to_cbor_hex(),
        wallet.vk.to_json(),
        wallet.sk.to_json(),
    )
    return wallet
