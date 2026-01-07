#!/usr/bin/env python3

from os import makedirs
from os.path import join, exists

KEYS_DIR = './keys'
makedirs(KEYS_DIR, exist_ok=True)

MY_SIGNING_KEY = join(KEYS_DIR, 'pubsub2.sk')
MY_PUBLIC_ADDR = join(KEYS_DIR, 'pubsub2.addr')
 
if exists(MY_SIGNING_KEY):
    print(f'found existing signing key {MY_SIGNING_KEY}')
    assert exists(MY_PUBLIC_ADDR)
else:
    from pycardano import Address, Network, PaymentSigningKey, PaymentVerificationKey
    signing_key = PaymentSigningKey.generate()
    signing_key.save(MY_SIGNING_KEY)
    verification_key = PaymentVerificationKey.from_signing_key(signing_key)
    address = Address(payment_part=verification_key.hash(), network=Network.TESTNET)
    with open(MY_PUBLIC_ADDR, "w") as f:
        f.write(str(address))
