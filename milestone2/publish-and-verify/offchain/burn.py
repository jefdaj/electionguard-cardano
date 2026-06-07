#!/usr/bin/env python3

'''Usage:
  burn.py <election_json> <key_dirs>...

Options:
  <election_json>  Path to the saved ElectionContext.
  <key_dirs>       One or more dirs to search for election keys. Only keys
                   matching the funder, admin, and subchannel publishers will
                   be loaded.
'''

import json
import os
import re
import time

from docopt import docopt
from glob import glob
from pprint import pformat, pprint
from typing import List, Mapping, Optional, Tuple

from pycardano import *
from egc import *

# TODO remove?
from egc.core.subscriber import *

import logging

logging.basicConfig(
  filename='burn.log',
  encoding='utf-8',
  level=logging.INFO,
  format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

LOG = logging.getLogger(os.path.basename(__file__))

ARGS = docopt(__doc__)
LOG.info(f'ARGS: {pformat(ARGS)}')

# TODO:
# 1. load funder addr from ctx
# 2. funder create own collateral if needed
# 3. start + stop a subscriber
# 4. get other addrs from sub state
# 5. load keys matching all addrs from disk from list of dirs
#    (error if any missing?)
# 6. sweep subchannel + admin collateral one at a time
# 7. burn stts and send all ada back to funder


### constants ###

FUNDER_CHANNEL_STR = 'funder'
ADMIN_CHANNEL_STR = ChannelIdHelper.to_string(ADMIN_CHANNEL_ID)


# For reference:
#     def ensure_own_collateral(self):
#         # Funder is the only node that needs to set its own collateral, I think?
#         # TODO but they should all test for it and throw a visible error if there isn't one
#         LOG.debug('Funder.ensure_own_collateral')
#         create_own_collateral(self.publisher.key_pair)
#         # TODO unify wait_for_collateral with Publisher.wait_for_confirmation
#         self.collateral_utxo = wait_for_collateral(self.publisher.key_pair.addr)

### load election context ###

CTX = ElectionContext.from_json(ARGS['<election_json>'])
LOG.debug(f'CTX:\n{pformat(CTX)}\n')

SCRIPT = CTX.script
LOG.info(f'SCRIPT: {SCRIPT}')

POLICY_ID = SCRIPT.policy_id
LOG.info(f'POLICY_ID: {POLICY_ID}')

# Keys already loaded from disk
KEYS_BY_ADDR: Mapping[Address, KeyPair] = {}

# Addrs we want to find keys for by channel_id
ADDRS_BY_ID: Mapping[str, Address] = {}
ADDRS_BY_ID[FUNDER_CHANNEL_STR] = CTX.deployment.funder_address # TODO already encoded, right?
LOG.info(f'ADDRS_BY_ID: {ADDRS_BY_ID}')


### get current on-chain channel states ###

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

# This is almost like SUB.states, but it uses str keys because technically
# 'funder' isn't a valid channel id.
STATES: Mapping[str, Tuple[UTxO, ChannelState]] = {
    ChannelIdHelper.to_string(channel_id): (channel_utxo, channel_state)
    for (channel_id, (channel_utxo, channel_state)) in SUB.states.items()
}
LOG.info(f'STATES keys: {pformat(STATES.keys())}')
LOG.info(f'admin state: {pformat(STATES[ADMIN_CHANNEL_STR][1])}')
raise SystemExit


### load destination wallet ###

KEYS_DIR=os.path.realpath(ARGS['<keys_dir>'])
PUB = ElectionPublisher(
    role       = 'burner',
    role_index = 1,
    keys_dir   = KEYS_DIR,
    key_name   = ARGS['<key_name>'],
)
LOG.info(f'PUB: {PUB}')


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

for (utxo, _) in SUB.states.values():
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

Are you sure? (y/n): '''

if confirm(prompt=MSG):
    try:
        LOG.info('\nBurning tokens...')
        BURN_TX = PUB.sign_and_submit(BURN_TXB)
        PUB.wait_for_confirmation(BURN_TX)
        LOG.info('done')
    except Exception as e:
        LOG.error(e)
        raise
else:
    LOG.error('NOT SURE. ABORT')
