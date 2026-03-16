#!/usr/bin/env python3

# TODO click interface
# TODO import static_records
# TODO write a "generate multiple keypairs" function in wallet (and start wallet)
# TODO if keys don't exist in --keys-dir: generate them, save files
# TODO separate script to send ADA from on secret key file -> another? or use eternl?
# TODO should be able to skip that if the admin already has ADA from a prev run
# TODO init a publisher (and start writing one lol)
# publisher should start in "not ready" mode, and you either:
# 1. tell it the oneshot utxo used (+ expected policy_id?)
# 2. tell it to InitElection itself using a utxo from the admin wallet
# TODO ... but for now can just assume the 2nd case because this is a one-off demo script
# TODO use publisher to InitElection
# TODO but first, print the info needed by the verifier and generate a qr code if easy
