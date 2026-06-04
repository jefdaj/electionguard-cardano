#!/usr/bin/env python3

'''Usage:
  ./publish.py <keys_dir> <funder_wallet_name>
'''

import os
from docopt import docopt
from pprint import pformat

from pycardano import *
from egc import *

from static_records import STATIC_PHASES, STATIC_TRANSACTIONS

import logging

logging.basicConfig(
  filename='publish.log',
  encoding='utf-8',
  level=logging.DEBUG,
  format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

LOG = logging.getLogger(os.path.basename(__file__))

LOG.debug(
  'admin phases by relative block:\n%s\n' %
  pformat(STATIC_PHASES)
)

LOG.debug(
  '(redeemer, records to post) by channel and relative block:\n%s\n' %
  pformat(STATIC_TRANSACTIONS)
)

args = docopt(__doc__)

# Keys will be arranged like:
# <keys_dir>/admin.{sk,addr}
# <keys_dir>/guardian1.{sk,addr}
# <keys_dir>/...
keys_dir=os.path.realpath(args['<keys_dir>'])

# The wallet which funds the election and recovers remaining ADA afterward.
# Often but not necesarily the personal wallet of the election admin.
# In a future web interface, this will be the wallet you connect to the dApp.
# For now, this loads my main dev wallet with tADA from the faucet.
funder_keys = KeyPair(keys_dir=keys_dir, name=args['<funder_wallet_name>'], verbose=False)
funder = Funder(key_pair=funder_keys)
# funder.init_script()
# LOG.info(f'oneshot_utxo: {funder.election.script.oneshot_utxo}')

# TODO for now, just create the admin keypair. admin itself can wait until election exists
# Create Admin separately in case it's a different person from the Funder.
admin_keys = KeyPair(keys_dir=keys_dir, name='admin', verbose=False)
# a = Admin(keys_dir)
# a._init_publisher(funder.script) # TODO make this less awkward

# TODO should this be hidden as part of init_election?
script = funder.init_script()

# Create the admin STT and run delayed admin init functions.
# Also returns info needed for a Subscriber to index election events.
init_tx = funder.init_election(script=script, admin_vkh=admin_keys.vkh, admin_ada=10)
LOG.debug(f'init_tx: {init_tx}')
LOG.debug(f'election_ctx: {funder.election_ctx}')

LOG.info(f'election deployed: {funder.election_ctx.deployment.to_dict()}')

funder.publisher.wait_for_confirmation(init_tx)
LOG.info('init_tx confirmed')

# TODO should the publisher just create and return this directly?
# sub_cfg = es.SubscriberConfig(
#   since_slot       = sub_info['slot'],
#   since_block_hash = sub_info['block_hash'],
#   policy_id        = funder.publisher.script.policy_id,
# )
# LOG.info(f'sub_cfg: {sub_cfg}')

# LOG.info('published init_tx')
# LOG.debug(f'full init_tx:\n%s\n' % pformat(init_tx))

# funder.publisher.wait_for_confirmation(init_tx)

# funder.burn_test_tokens()

# TODO test this
# funder.burn_test_tokens()

# TODO finish writing the rest of this
# a.post_manifest()
#
# shared_args = {
#     'keys_dir': keys_dir,
#     'ogmios': ogmios,
#     'kupo_info': kupo_info,
# }
#
# g1 = egc.roles.Guardian(index=1, **shared_args)
# g2 = egc.roles.Guardian(index=2, **shared_args)
# g3 = egc.roles.Guardian(index=3, **shared_args)
# d1 = egc.roles.Device(  index=1, **shared_args)
# v1 = egc.roles.Verifier(index=1, **shared_args)
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
