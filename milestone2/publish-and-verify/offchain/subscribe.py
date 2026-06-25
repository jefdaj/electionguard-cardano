#!/usr/bin/env python3

'''Usage:
  ./subscribe.py <policy_id> <slot> <block_hash>
'''

import os
from pprint import pformat
from pycardano import *
import logging
import time
from pprint import pformat
from docopt import docopt

# import ecg
# from ecg import subscriber as es
# from ecg.plutus.types.channel import ADMIN_CHANNEL_ID
from egc import *
from egc.core.subscriber import *

import logging

logging.basicConfig(
  # filename='subscribe.log',
  encoding='utf-8',
  level=logging.INFO,
  format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

# logging.getLogger('urllib3').setLevel(logging.DEBUG)

LOG = logging.getLogger(os.path.basename(__file__))

args = docopt(__doc__)

sub_cfg = SubscriberConfig(
    since_slot = args['<slot>'],
    since_block_hash = args['<block_hash>'],
    policy_id = ScriptHash(bytes.fromhex(args['<policy_id>'])),
)
LOG.info(f'sub_cfg:\n\n{pformat(sub_cfg)}\n')

def log_event(event: ChannelEvent):
    LOG.info('\n' + pformat(event) + '\n')

sub = ElectionSubscriber(
    sub_cfg,
    on_action=log_event,
)

sub.start()

# TODO this doesn't quite behave right: Ctrl-C quits without printing
prev = (None, None)
while not sub.is_done():
    try:
        (_, prev_recs) = prev
        states = sub.current_states()
        records = sub.all_records()
        new_recs = [str(r) for r in records if not r in prev_recs]
        cur = (states, records)
        if cur != prev:
            LOG.info(f'current states:\n\n{pformat(states)}\n')
            if new_recs:
                LOG.info('new records:')
                for r in new_recs:
                    LOG.info(r)
            prev = cur
        sub.sleep(3)
    except KeyboardInterrupt:
        LOG.warning('Got keyboard interrupt')
        break
LOG.info('Stopping...')
sub.stop()
sub.join()
