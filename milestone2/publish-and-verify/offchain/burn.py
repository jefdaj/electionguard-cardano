#!/usr/bin/env python3

'''Usage:
  ./burn.py <slot> <block_hash> <policy_id> <dest_addr>
'''

import logging
import os
from docopt import docopt
from pycardano import Redeemer, ScriptHash
from election.plutus import types as ept
from election import subscriber as es

logging.basicConfig(
  encoding='utf-8',
  level=logging.DEBUG,
  format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

# TODO consistent variable name casing

LOG = logging.getLogger(os.path.basename(__file__))

args = docopt(__doc__)


### subscribe to find latest admin stt utxo ###

sub_cfg = es.SubscriberConfig(
    since_slot = args['<slot>'],
    since_block_hash = args['<block_hash>'],
    policy_id = ScriptHash(bytes.fromhex(args['<policy_id>'])),
)
LOG.info(f'sub_cfg: {sub_cfg}')

sub = es.Subscriber(sub_cfg, es.handle_match, es.handle_endelection)
sub.start()
time.sleep(3)
sub.stop()
LOG.info(f'final history:\n{pformat(sub.history)}')

records = sub.subscribed_records()
LOG.info(f'final records: {pformat(records)}')


### create tx to burn and sweep funds ###

redeemer = Redeemer(data=ept.BurnTestTokens())
LOG.debug(f'redeemer: {redeemer}')
