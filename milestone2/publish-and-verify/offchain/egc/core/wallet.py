"""Generate and manage test wallets.

Expects that there will be one main dev wallet with a supply of (t)ADA,
and then lots of temporary test wallets. To avoid accidentally losing ADA
to failed tests, it saves copies of all generated keys.
This can be turned off by setting SAVE_BACKUPS=False.

Temporary wallets are distinguished first by their KEYS_DIR, which should be
unique at least per test, and then optionally by election role + index.

Example of a main wallet and two different valid test layouts:

keys/
├── main.addr
├── main.sk
├── test001
│   ├── admin.addr
│   ├── admin.sk
│   ├── device1.addr
│   ├── device1.sk
│   ├── guardian1.addr
│   ├── guardian1.sk
│   ├── guardian2.addr
│   ├── guardian2.sk
│   ├── verifier1.addr
│   └── verifier1.sk
└── test002
    ├── admin
    │   ├── admin.addr
    │   └── admin.sk
    ├── device1
    │   ├── device1.addr
    │   └── device1.sk
    ├── guardian1
    │   ├── guardian1.addr
    │   └── guardian1.sk
    ├── guardian2
    │   ├── guardian2.addr
    │   └── guardian2.sk
    └── verifier1
        ├── verifier1.addr
        └── verifier1.sk

The test001 format is simplest for pytest, but something more like test002
makes sense when generating each keypair in a separate docker data mount dir.
"""

from pathlib import Path
import logging

LOG = logging.getLogger(__name__)

from pycardano import *
# from pycardano import Address, Network, SigningKey, PaymentSigningKey, PaymentVerificationKey, VerificationKeyHash

DEF_KEYS_DIR = Path(__file__).parent.parent.parent / 'keys'

def vkh_for_signing_key(sk: PaymentSigningKey) -> VerificationKeyHash:
    verification_key = PaymentVerificationKey.from_signing_key(sk)
    return verification_key.hash()

def addr_for_signing_key(sk: PaymentSigningKey) -> Address:
    verification_key = PaymentVerificationKey.from_signing_key(sk)
    address = Address(payment_part=verification_key.hash(), network=Network.TESTNET)
    return address

def load_wallet_address(keys_dir=DEF_KEYS_DIR, name="main", verbose=False) -> Address:
    keys_dir = Path(keys_dir)
    public_addr = (keys_dir / (name + '.addr')).absolute()
    if not public_addr.exists():
        generate_keypair(keys_dir=keys_dir, name=name, verbose=verbose)
    with public_addr.open('r') as f:
        return Address.from_primitive(f.read())

def load_wallet_signing_key(keys_dir=DEF_KEYS_DIR, name='main', verbose=False) -> SigningKey:
    keys_dir = Path(keys_dir)
    signing_key = (keys_dir / (name + '.sk')).absolute()
    if not signing_key.exists():
        generate_keypair(keys_dir=keys_dir, name=name, verbose=verbose)
    with signing_key.open('r') as f:
        # TODO would validate_type=True here help?
        return SigningKey.from_json(f.read())

def load_keypair(keys_dir=DEF_KEYS_DIR, name='main', verbose=True) -> (SigningKey, Address):
    LOG.debug('load_keypair')
    keys_dir = Path(keys_dir)
    sk   = load_wallet_signing_key(keys_dir=keys_dir, name=name, verbose=verbose)
    addr = load_wallet_address(keys_dir=keys_dir, name=name, verbose=verbose)
    return (sk, addr)

def generate_keypair(keys_dir=DEF_KEYS_DIR, name='main', verbose=True) -> (SigningKey, Address):
    LOG.debug('generate_keypair')
    keys_dir = Path(keys_dir)
    sk_path   = (keys_dir / (name + '.sk'  )).absolute()
    addr_path = (keys_dir / (name + '.addr')).absolute()
    if sk_path.exists():
        LOG.debug(f'sk_path exists: {sk_path}')
        assert addr_path.exists()
        LOG.debug(f'addr_path exists: {addr_path}')
        return load_keypair(keys_dir=keys_dir, name=name, verbose=verbose)
    keys_dir.mkdir(exist_ok=True)
    signing_key = PaymentSigningKey.generate()
    signing_key.save(str(sk_path))
    address = addr_for_signing_key(signing_key)
    with addr_path.open("w") as f:
        f.write(str(address))
    msg = f'''
    Your new Preview testnet keys are here:

    {sk_path}
    {addr_path}

    Your public address (2nd file) is: {address}

    If this is your main dev wallet, go fund that address with tADA from the
    faucet before running any tests:
    https://docs.cardano.org/cardano-testnets/tools/faucet

    If you don't, local tests will still work but testnet tests will fail.
    '''
    LOG.info(msg)
    if verbose:
        print(msg)
    return (signing_key, address)
 
class KeyPair:
    def __init__(self, keys_dir=DEF_KEYS_DIR, name='main', verbose=True):
        LOG.debug('KeyPair.__init__')
        (sk, addr) = generate_keypair(keys_dir=keys_dir, name=name, verbose=verbose)
        self.sk = sk
        self.addr = addr
        self.vkh = vkh_for_signing_key(self.sk)
    # TODO repr?
