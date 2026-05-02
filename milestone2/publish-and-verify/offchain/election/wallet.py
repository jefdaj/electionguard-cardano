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

from os import makedirs
from os.path import basename, exists, join, realpath
from pathlib import Path
from pycardano import Address, Network, SigningKey, PaymentSigningKey, PaymentVerificationKey, VerificationKeyHash

KEYS_DIR = Path(__file__).parent / '../keys'
SIGNING_KEY = join(KEYS_DIR, 'main.sk')
PUBLIC_ADDR = join(KEYS_DIR, 'main.addr')

def vkh_for_signing_key(sk: PaymentSigningKey) -> VerificationKeyHash:
    verification_key = PaymentVerificationKey.from_signing_key(sk)
    return verification_key.hash()

def addr_for_signing_key(sk: PaymentSigningKey) -> Address:
    verification_key = PaymentVerificationKey.from_signing_key(sk)
    address = Address(payment_part=verification_key.hash(), network=Network.TESTNET)
    return address

def generate_keys():
    if exists(SIGNING_KEY):
        assert exists(PUBLIC_ADDR)
        return
    makedirs(KEYS_DIR, exist_ok=True)
    signing_key = PaymentSigningKey.generate()
    signing_key.save(SIGNING_KEY)
    address = addr_for_signing_key(signing_key)
    with open(PUBLIC_ADDR, "w") as f:
        f.write(str(address))
    msg = f'''
    Your new Preview testnet keys are here:

    {realpath(SIGNING_KEY)}
    {realpath(PUBLIC_ADDR)}

    Your public address (2nd file) is: {address}

    Before continuing, fund that address with tADA from the faucet:
    https://docs.cardano.org/cardano-testnets/tools/faucet

    If you don't, local tests will still work but testnet tests will fail.
    '''
    input(msg)
 
def load_wallet_addr(name="main") -> Address:
    generate_keys()
    with open(PUBLIC_ADDR, 'r') as f:
        return Address.from_primitive(f.read())

def load_election_wallet_signing_key() -> SigningKey:
    generate_keys()
    with open(SIGNING_KEY, 'r') as f:
        # TODO would validate_type=True here help?
        return SigningKey.from_json(f.read())
