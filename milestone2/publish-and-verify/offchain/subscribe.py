#!/usr/bin/env python3

import os
from pprint import pformat
from pycardano import *
import logging
import time

import election
from election import subscriber as es

logging.basicConfig(
  filename='subscribe.log',
  encoding='utf-8',
  level=logging.DEBUG,
  format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

LOG = logging.getLogger(os.path.basename(__file__))

# hardcoded for first attempt:
sub_cfg = es.SubscriberConfig(
  since_slot=113207279,
  since_block_hash='c3f7c1c929acb74da0ae89a08d5c04ea6e46a221779d2d1483c93c9001f8f254',
  policy_id=ScriptHash(bytes.fromhex('1188a63f2d316c907cb09926f8072a7f37e2ce8f02a0dedc99ceda0f')),
  until_slot=None
)
LOG.info(f'sub_cfg: {sub_cfg}')

sub = es.Subscriber(sub_cfg, es.handle_match, es.handle_endelection)
sub.start()
time.sleep(1)
sub.stop()
records = sub.subscribed_records()
LOG.info(f'records: {records}')
