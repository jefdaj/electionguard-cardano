from os import makedirs
from os.path import basename, exists, join, realpath
from pathlib import Path
from pycardano import Address, Network, SigningKey, PaymentSigningKey, PaymentVerificationKey

KEYS_DIR = Path(__file__).parent / '../../keys'
SIGNING_KEY = join(KEYS_DIR, 'pubsub2.sk')
PUBLIC_ADDR = join(KEYS_DIR, 'pubsub2.addr')

def addr_for_signing_key(sk: PaymentSigningKey) -> Address:
    verification_key = PaymentVerificationKey.for_signing_key(signing_key)
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
 
def load_test_wallet_addr() -> Address:
    generate_keys()
    with open(PUBLIC_ADDR, 'r') as f:
        return Address.from_primitive(f.read())

def load_test_wallet_signing_key() -> SigningKey:
    generate_keys()
    with open(SIGNING_KEY, 'r') as f:
        # TODO would validate_type=True here help?
        return SigningKey.from_json(f.read())
