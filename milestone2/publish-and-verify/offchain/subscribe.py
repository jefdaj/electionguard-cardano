#!/usr/bin/env python3

'''Usage:
  ./subscribe.py <slot> <block_hash> <policy_id>
'''

import os
from pprint import pformat
from pycardano import *
import logging
import time
from pprint import pformat
from docopt import docopt

import ecg
from ecg import subscriber as es
from ecg.plutus.types.channel import ADMIN_CHANNEL_ID

logging.basicConfig(
  # filename='subscribe.log',
  encoding='utf-8',
  level=logging.DEBUG,
  format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

LOG = logging.getLogger(os.path.basename(__file__))

args = docopt(__doc__)

sub_cfg = es.SubscriberConfig(
    since_slot = args['<slot>'],
    since_block_hash = args['<block_hash>'],
    policy_id = ScriptHash(bytes.fromhex(args['<policy_id>'])),
)
LOG.info(f'sub_cfg: {sub_cfg}')

# TODO does handle_endelection need to be separate? maybe combine after all
sub = es.Subscriber(sub_cfg, es.handle_match, es.handle_endelection)
sub.start()
time.sleep(1)
sub.stop()
LOG.info(f'final history:\n{pformat(sub.history)}')

records = sub.subscribed_records(ADMIN_CHANNEL_ID)
LOG.info(f'final records: {pformat(records)}')
