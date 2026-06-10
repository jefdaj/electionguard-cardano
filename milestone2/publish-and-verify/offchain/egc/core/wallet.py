"""Generate and manage wallets with a focus on testing.

Expects that there will be one main dev wallet with a supply of (t)ADA,
and then lots of temporary test wallets.

When EGC_MODE=test, it will:

- leave of generated keys in the tmpdir (normally /tmp/nix-shell.XXXXX)
- log signing keys to <keys_dir>/test-keys.log
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Self, Tuple
from dataclasses import dataclass
from pycardano import *
from .config import IS_TEST
import logging


DEF_KEYS_DIR = Path(__file__).parent.parent.parent / 'keys'

# Regular logger
LOG = logging.getLogger(__name__)

# Separate logger for test keys
KEYS_LOG = logging.getLogger('test-keys')
if IS_TEST:
    keys_fh = logging.FileHandler(DEF_KEYS_DIR / 'test-keys.log')
    keys_fh.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    KEYS_LOG.addHandler(keys_fh)
    KEYS_LOG.setLevel(logging.DEBUG)
    del keys_fh
    KEYS_LOG.debug('Running with EGC_MODE=test')
else:
    KEYS_LOG.setLevel(logging.CRITICAL + 1)
    KEYS_LOG.propagate = False
    KEYS_LOG.critical('IF YOU CAN READ THIS, YOU MAY BE LEAKING PRIVATE KEYS!')


@dataclass(frozen=True, slots=True)
class Wallet:
    """A convenience bundle around a Cardano `SigningKey`.

    Everything except `sk` is derived, so equality, serialization, and
    persistence are all driven by the signing key alone.
    """

    sk:   SigningKey
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
    def from_sk_path(cls, sk_path: Path) -> Self:
        LOG.debug('Wallet.from_sk_path: %s', sk_path)
        return cls.from_json(Path(sk_path).read_text())

    @classmethod
    def load_or_create(
        cls,
        keys_dir: Path = DEF_KEYS_DIR,
        name: str = 'default',
        verbose: bool = True,
    ) -> Self:
        """Load the wallet named `name` from `keys_dir`, generating it if absent."""
        keys_dir = Path(keys_dir)
        sk_path = keys_dir / f'{name}.sk'

        if sk_path.exists():
            LOG.debug('sk_path exists; loading: %s', sk_path)
            return load_wallet(sk_path)

        return create_wallet(keys_dir=keys_dir, name=name, verbose=verbose)

    def to_json(self, *args, **kwargs) -> str:
        return self.sk.to_json(*args, **kwargs)

    def save(self, sk_path: Path) -> None:
        Path(sk_path).write_text(self.to_json())

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

def load_wallet(sk_path: Optional[Path] = None, keys_dir=DEF_KEYS_DIR, name='default') -> Wallet:
    LOG.debug('load_wallet')
    if sk_path is None:
        keys_dir = Path(keys_dir)
        sk_path = keys_dir / f'{name}.sk'
    return Wallet.from_sk_path(sk_path)

def load_wallet_by_address(address: Address, keys_dir=DEF_KEYS_DIR) -> Optional[Tuple[Path, Wallet]]:
    "Mainly to help return collateral in test fixtures."
    LOG.debug('load_wallet_for_address')
    keys_dir = Path(keys_dir)
    for sk_path in sorted(keys_dir.glob('*.sk')):
        w = Wallet.from_sk_path(sk_path)
        if w.addr == address:
            return (sk_path, w)
    return None

def create_wallet(keys_dir=DEF_KEYS_DIR, name='default', verbose=True) -> Wallet:
    LOG.debug('create_wallet')
    keys_dir = Path(keys_dir)
    sk_path   = keys_dir / f'{name}.sk'
    addr_path = keys_dir / f'{name}.addr'
    if sk_path.exists() or addr_path.exists():
        err = f'ERROR: at least one wallet file already exists: {sk_path}, {addr_path}'
        LOG.error(err)
        raise Exception(err)
    keys_dir.mkdir(exist_ok=True)
    signing_key = PaymentSigningKey.generate()
    signing_key.save(str(sk_path))
    LOG.info(f'Generated {sk_path}')
    wallet = Wallet.from_sk_path(sk_path)
    msg = f'''
    Your new Preview testnet key is here:

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
        '  addr = %s\n'
        '  vkh  = %s\n'
        '  vk   = %s\n'
        '  sk   = %s\n',
        name,
        wallet.addr,
        wallet.vkh.to_cbor_hex(),
        wallet.vk.to_json(),
        wallet.sk.to_json(),
    )
    return wallet
