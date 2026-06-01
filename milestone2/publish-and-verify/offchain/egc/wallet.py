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
from pycardano import Address, Network, SigningKey, PaymentSigningKey, PaymentVerificationKey, VerificationKeyHash

DEF_KEYS_DIR = Path(__file__).parent / '../keys'

def vkh_for_signing_key(sk: PaymentSigningKey) -> VerificationKeyHash:
    verification_key = PaymentVerificationKey.from_signing_key(sk)
    return verification_key.hash()

def addr_for_signing_key(sk: PaymentSigningKey) -> Address:
    verification_key = PaymentVerificationKey.from_signing_key(sk)
    address = Address(payment_part=verification_key.hash(), network=Network.TESTNET)
    return address

def generate_keys(keys_dir=DEF_KEYS_DIR, name='main', verbose=True):
    keys_dir = Path(keys_dir)
    sk_path   = (keys_dir / (name + '.sk'  )).absolute()
    addr_path = (keys_dir / (name + '.addr')).absolute()
    if sk_path.exists():
        assert addr_path.exists()
        return
    keys_dir.mkdir(exist_ok=True)
    signing_key = PaymentSigningKey.generate()
    signing_key.save(str(sk_path))
    address = addr_for_signing_key(signing_key)
    with addr_path.open("w") as f:
        f.write(str(address))
    msg = f'''
    Your new Preview testnet keys are here:

    {signing_key}
    {address}

    Your public address (2nd file) is: {str(addr_path)}

    Before continuing, fund that address with tADA from the faucet:
    https://docs.cardano.org/cardano-testnets/tools/faucet

    If you don't, local tests will still work but testnet tests will fail.
    '''
    if verbose:
        print(msg)
 
def load_wallet_addr(keys_dir=DEF_KEYS_DIR, name="main", verbose=False) -> Address:
    keys_dir = Path(keys_dir)
    generate_keys(keys_dir=keys_dir, name=name, verbose=verbose)
    public_addr = (keys_dir / (name + '.addr')).absolute()
    with public_addr.open('r') as f:
        return Address.from_primitive(f.read())

def load_wallet_signing_key(keys_dir=DEF_KEYS_DIR, name='main', verbose=False) -> SigningKey:
    keys_dir = Path(keys_dir)
    generate_keys(keys_dir=keys_dir, name=name, verbose=verbose)
    signing_key = (keys_dir / (name + '.sk')).absolute()
    with signing_key.open('r') as f:
        # TODO would validate_type=True here help?
        return SigningKey.from_json(f.read())

# TODO Keypair class to encapsulate a lot of this?
