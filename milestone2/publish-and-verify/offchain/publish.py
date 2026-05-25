#!/usr/bin/env python3

import os
from pprint import pformat
import logging

import election
from static_records import STATIC_PHASES, STATIC_TRANSACTIONS

logging.basicConfig(
  filename='publish.log',
  encoding='utf-8',
  level=logging.DEBUG,
  format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

log = logging.getLogger(os.path.basename(__file__))

log.debug(
  'admin phases by relative block:\n%s\n' %
  pformat(STATIC_PHASES)
)

log.debug(
  '(redeemer, records to post) by channel and relative block:\n%s\n' %
  pformat(STATIC_TRANSACTIONS)
)

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

# Keys will be arranged like:
# test_keys/admin.{sk,addr}
# test_keys/guardian1.{sk,addr}
# test_keys/...
# test_keys = 'test_keys'
keys_dir='test-keys'

# The wallet which funds the election and recovers remaining ADA afterward.
# Often but not necesarily the personal wallet of the election admin.
# In a future web interface, this will be the wallet you connect to the dApp.
f = election.roles.funder.Funder(keys_dir, wallet_name='dev')

# Create Admin separately in case it's a different person from the Funder.
a = election.roles.admin.Admin(keys_dir)

# Create the admin STT and run delayed admin init functions.
# Also returns info needed for a Subscriber to index election events.
# TODO sub_info not implemented yet
sub_info = f.init_election(admin=a)

f.burn_test_tokens()

raise SystemExit

# TODO test this
# f.burn_test_tokens()

# TODO finish writing the rest of this
# a.post_manifest()
#
# shared_args = {
#     'keys_dir': keys_dir,
#     'ogmios': ogmios,
#     'kupo_info': kupo_info,
# }
#
# g1 = election.roles.Guardian(index=1, **shared_args)
# g2 = election.roles.Guardian(index=2, **shared_args)
# g3 = election.roles.Guardian(index=3, **shared_args)
# d1 = election.roles.Device(  index=1, **shared_args)
# v1 = election.roles.Verifier(index=1, **shared_args)
#
# # TODO later, move this after adding subchannels? that way n guardians is known
# # TODO also advance phase here?
# a.publish_ceremony_details(n_guardians=3, threshold=2)
#
# # how much ada to send from main wallet -> admin during init
# oneshot_ada = 100
#
# # how much ada to send from admin -> each subchannel
# channel_ada = 20
#
# subchannel_info = [(r.channel_id, r.vkh, channel_ada) for r in [g1, g2, g3, d1, v1]]
# subchannel_ids  = [c[0] for c in subchannels]
#
# a.add_subchannels(subchannel_info)
