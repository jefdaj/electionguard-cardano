#!/usr/bin/env python3

import os

sk_path = "keys/me.sk"
if os.path.exists(sk_path):
    raise Exception(f'abort because {sk_path} already exists')

from pycardano import Address, Network, PaymentSigningKey, PaymentVerificationKey

signing_key = PaymentSigningKey.generate()
signing_key.save(sk_path)
verification_key = PaymentVerificationKey.from_signing_key(signing_key)
 
address = Address(payment_part=verification_key.hash(), network=Network.TESTNET)
with open("keys/me.addr", "w") as f:
    f.write(str(address))
