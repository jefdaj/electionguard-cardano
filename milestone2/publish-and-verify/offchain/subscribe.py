#!/usr/bin/env python3

'''Usage:
  ./subscribe.py <policy_id> <slot> <block_hash>
'''

# TODO this doesn't quite behave right: Ctrl-C quits without printing

import os
from pprint import pformat
from pycardano import *
import logging
import time
from pprint import pformat
from docopt import docopt
import shutil

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
  # format="%(asctime)s %(levelname)s %(name)s: %(message)s",
  format="%(message)s",
)

# logging.getLogger('urllib3').setLevel(logging.DEBUG)

LOG = logging.getLogger(os.path.basename(__file__))

args = docopt(__doc__)

sub_cfg = SubscriberConfig(
    since_slot = args['<slot>'],
    since_block_hash = args['<block_hash>'],
    policy_id = ScriptHash(bytes.fromhex(args['<policy_id>'])),
)
LOG.info(f'\n{pformat(sub_cfg)}\n')

# one dir up when called from offchain
PUB_DIR = Path('../data/verifier2')

def log_and_fetch(event: ChannelEvent):
    LOG.debug('\n' + pformat(event) + '\n')
    if not event.output_state:
        return
    new_records = event.output_state.state.new_records
    paths = ipfs_fetch_records_to_file_sync(new_records, PUB_DIR)
    for (r,p) in zip(new_records, paths):
        LOG.info(f'{r} -> {p}')

sub = ElectionSubscriber(
    sub_cfg,
    on_action=log_and_fetch,
)

sub.start()

def log_srp_diff(prev, cur):
    (_, prev_recs, prev_phase) = prev
    (states, records, phase) = cur
    new_recs = [str(r) for r in records if not r in prev_recs]
    if cur != prev:
        LOG.debug(f'Current states:\n\n{pformat(states)}\n')
        if new_recs:
            LOG.debug('New records:')
            for r in new_recs:
                LOG.debug(r)
        if phase != prev_phase:
            LOG.debug(f'Current phase: {phase}')
 
prev = (None, None, None)

while not sub.is_done():
    try:
        states  = sub.current_states()
        records = sub.all_records()
        phase   = sub.current_phase()
        cur = (states, records, phase)
        log_srp_diff(prev, cur)
        prev = cur
        sub.sleep(3)
    except KeyboardInterrupt:
        LOG.warning('Got keyboard interrupt')
        break

sub.join()

recs = sub.all_records()
print(f'{len(recs)} records total:')
for r in recs:
    print(str(r))
