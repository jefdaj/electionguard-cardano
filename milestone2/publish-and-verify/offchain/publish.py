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

main_keys = 'main_keys'

# Keys will be arranged like:
# test_keys/admin.{sk,addr}
# test_keys/guardian1.{sk,addr}
# test_keys/...
test_keys = 'test_keys'

# one shared cardano-node-ogmios instance for everyone, for now
ogmios = ...

a = election.roles.Admin(keys_dir, ogmios)

kupo_info = a.init_election(main_keys, test_keys, oneshot_ada)

a.post_manifest()

shared_args = {
    'keys_dir': keys_dir,
    'ogmios': ogmios,
    'kupo_info': kupo_info,
}

g1 = election.roles.Guardian(index=1, **shared_args)
g2 = election.roles.Guardian(index=2, **shared_args)
g3 = election.roles.Guardian(index=3, **shared_args)
d1 = election.roles.Device(  index=1, **shared_args)
v1 = election.roles.Verifier(index=1, **shared_args)

# TODO later, move this after adding subchannels? that way n guardians is known
# TODO also advance phase here?
a.publish_ceremony_details(n_guardians=3, threshold=2)

# how much ada to send from main wallet -> admin during init
oneshot_ada = 100

# how much ada to send from admin -> each subchannel
channel_ada = 20

subchannel_info = [(r.channel_id, r.vkh, channel_ada) for r in [g1, g2, g3, d1, v1]]
subchannel_ids  = [c[0] for c in subchannels]

a.add_subchannels(subchannel_info)
