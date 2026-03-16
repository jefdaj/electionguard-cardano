#!/usr/bin/env python3

from pprint import pprint
from static_records_py_out import STATIC_PHASES, STATIC_TRANSACTIONS

print('admin phases by relative block:'); pprint(STATIC_PHASES)
print('\n(redeemer, records to post) by channel and relative block:'); pprint(STATIC_TRANSACTIONS)

# TODO start a click interface with --keys-dir

# TODO write a "generate multiple keypairs" function in wallet (and start wallet)
# TODO if keys don't exist in --keys-dir:
#        - gen 1 keypair per role: amdmin, guardian1, guardian2, guardian3, device1, verifier1
#        - save files

# TODO separate script to send ADA from on secret key file -> another? or use eternl?
# TODO should be able to skip that if the admin already has ADA from a prev run

# TODO init a publisher
# publisher should start in "not ready" mode, and you either:
# 1. tell it the oneshot utxo used (+ expected policy_id?)
# 2. tell it to InitElection itself using a utxo from the admin wallet
# but for now can just assume the 2nd case because this is a one-off demo script

# TODO print the info needed by the verifier and generate a qr code if easy

# TODO use publisher to InitElection
