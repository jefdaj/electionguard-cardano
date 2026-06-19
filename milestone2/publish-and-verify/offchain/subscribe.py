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
  level=logging.DEBUG,
  format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

LOG = logging.getLogger(os.path.basename(__file__))

args = docopt(__doc__)

sub_cfg = SubscriberConfig(
    since_slot = args['<slot>'],
    since_block_hash = args['<block_hash>'],
    policy_id = ScriptHash(bytes.fromhex(args['<policy_id>'])),
)
LOG.info(f'sub_cfg: {sub_cfg}')

def log_event(event: ChannelEvent):
    LOG.info('\n' + pformat(event) + '\n')

sub = ElectionSubscriber(
    sub_cfg,
    on_action=log_event,
)
sub.start()

def log_current():
    channel_ids = sub.current_channel_ids()
    LOG.info(f'current_channel_ids: {channel_ids}')
    for ch_id in channel_ids:
        ch_str = channel_id_to_string(ch_id)
        ch_state = sub.current_state(ch_id)
        LOG.info(f'current {ch_str} state: {ch_state}')

while not sub.is_done():
    log_current()
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        sub.stop()
        break

sub.join()

LOG.info(f'final history:\n\n{pformat(sub.history)}\n')
