#!/usr/bin/env python3

'''Usage:
  ./burn.py <keys_dir> <key_name> <election_context_json>
'''

import json
import os
import re
import time

from docopt import docopt
from glob import glob
from pprint import pformat
from typing import Optional

from pycardano import *
from egc import *
from egc.core.subscriber import *

import logging

logging.basicConfig(
  filename='burn.log',
  encoding='utf-8',
  level=logging.DEBUG,
  format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

LOG = logging.getLogger(os.path.basename(__file__))

ARGS = docopt(__doc__)


### load election context ###

CTX = ElectionContext.from_json(ARGS['<election_context_json>'])
LOG.debug(f'CTX:\n{pformat(CTX)}\n')

SCRIPT = CTX.script
LOG.info(f'SCRIPT: {SCRIPT}')

POLICY_ID = SCRIPT.policy_id
LOG.info(f'POLICY_ID: {POLICY_ID}')


### load destination wallet ###

KEYS_DIR=os.path.realpath(ARGS['<keys_dir>'])
PUB = ElectionPublisher(
    role       = 'burner',
    role_index = 1,
    keys_dir   = KEYS_DIR,
    key_name   = ARGS['<key_name>'],
)
LOG.info(f'PUB: {PUB}')


### subscribe to find latest utxos ###

SUB_CFG = SubscriberConfig(
    since_slot       = CTX.deployment.index_from_slot,
    since_block_hash = CTX.deployment.index_from_block_hash,
    policy_id        = SCRIPT.policy_id,
)
LOG.info(f'SUB_CFG: {SUB_CFG}')

SUB = ElectionSubscriber(SUB_CFG)
SUB.start()
time.sleep(3)
SUB.stop()

LOG.info(f'final utxos: {pformat(SUB.utxos)}')


### create tx to burn and sweep funds ###

MINT_REDEEMER = Redeemer(data=BurnTestTokens())
LOG.debug(f'MINT_REDEEMER: {MINT_REDEEMER}')

CHANNEL_IDS = list(SUB.states.keys())
LOG.info(f'CHANNEL_IDS: {CHANNEL_IDS}')

BURN_ASSETS = mint_channel_stt_assets(
    SCRIPT.policy_id,
    -1,
    CHANNEL_IDS,
)
LOG.info(f'BURN_ASSETS: {BURN_ASSETS}')

BURN_TXB = (
    TransactionBuilder(OGMIOS_CTX, mint=BURN_ASSETS)
    .add_minting_script(script=SCRIPT.mint_script, redeemer=MINT_REDEEMER)
)

for utxo in SUB.utxos.values():
    LOG.debug(f'utxo: {utxo}')
    spend_redeemer = Redeemer(data=BurnTestTokens())
    BURN_TXB = BURN_TXB.add_script_input(utxo, script=SCRIPT.spend_script, redeemer=spend_redeemer)

LOG.debug('BURN_TXB:\n%s\n' % pformat(BURN_TXB))


### confirm, then submit tx ###

def confirm(prompt="Are you sure? (y/n): "):
    return input(prompt).strip().lower() in ("y", "yes")

MSG = f'''
About to burn these tokens:
{pformat(BURN_ASSETS)}

Channel ADA will be sent to {PUB.key_pair.addr}

Are you sure? (y/n):'''

if confirm(prompt=MSG):
    try:
        BURN_TX = PUB.sign_and_submit(BURN_TXB)
        PUB.wait_for_confirmation(BURN_TX)
    except Exception as e:
        LOG.error(e)
        raise
else:
    LOG.error('NOT SURE. ABORT')
