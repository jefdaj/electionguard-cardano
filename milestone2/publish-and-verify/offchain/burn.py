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
LOG.debug(f'ARGS: {pformat(ARGS)}')

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

# TODO do we actually need the funder private key at all?
# FUNDER_CHANNEL_STR = 'funder'
ADMIN_CHANNEL_STR = channel_id_to_string(ADMIN_CHANNEL_ID)


### load election context ###

CTX = ElectionContext.from_json(ARGS['<election_json>'])
LOG.debug(f'CTX:\n{pformat(CTX)}\n')

SCRIPT = CTX.script
LOG.debug(f'SCRIPT: {SCRIPT}')

POLICY_ID = SCRIPT.policy_id
LOG.debug(f'POLICY_ID: {POLICY_ID}')

# Keys already loaded from disk
KEYS_BY_STR: Mapping[str, KeyPair] = {}

# Addrs we want to find keys for by channel_str
ADDRS_BY_STR: Mapping[str, Address] = {}
# ADDRS_BY_STR[FUNDER_CHANNEL_STR] = CTX.deployment.funder_address # TODO already encoded, right?


### get current on-chain channel states ###

SUB_CFG = SubscriberConfig(
    since_slot       = CTX.deployment.index_from_slot,
    since_block_hash = CTX.deployment.index_from_block_hash,
    policy_id        = SCRIPT.policy_id,
)
LOG.debug(f'SUB_CFG: {SUB_CFG}')

SUB = ElectionSubscriber(SUB_CFG)
SUB.start()
time.sleep(1)
SUB.stop()

# This is almost like SUB.states, but it uses str keys because technically
# 'funder' isn't a valid channel id.
STATES: Mapping[str, Tuple[UTxO, ChannelState]] = {
    channel_id_to_string(channel_id): (channel_utxo, channel_state)
    for (channel_id, (channel_utxo, channel_state)) in SUB.states.items()
}
LOG.debug(f'STATES keys: {pformat(STATES.keys())}')
LOG.debug(f'admin state: {pformat(STATES[ADMIN_CHANNEL_STR][1])}')


### figure out which keys to look for ###

# TODO move to a util function, but where?
for (channel_str, (_, channel_wrap)) in sorted(STATES.items()):
    if channel_str == 'admin':
        vkh_bytes = channel_wrap.state.admin
    else:
        vkh_bytes = channel_wrap.state.publisher
    vkh = VerificationKeyHash(vkh_bytes)
    addr = Address(payment_part=vkh, network=Network.TESTNET)
    ADDRS_BY_STR[channel_str] = addr

LOG.debug(f'ADDRS_BY_STR:\n{pformat(ADDRS_BY_STR)}')


### load keys ###

SK_PATHS = []
for key_dir in ARGS['<key_dirs>']:
    SK_PATHS += glob(os.path.join(key_dir, '*.sk'))
SK_PATHS = sorted(SK_PATHS)
LOG.debug(f'SK_PATHS: {SK_PATHS}')

for sk_path in SK_PATHS:
    keys_dir = os.path.dirname(sk_path)
    key_name = os.path.splitext(os.path.basename(sk_path))[0]
    keys = KeyPair(keys_dir, key_name)
    for (s, a) in ADDRS_BY_STR.items():
        if keys.addr == a:
            KEYS_BY_STR[s] = keys
LOG.debug(f'KEYS_BY_STR:\n{pformat(KEYS_BY_STR)}')

for needed_str in ADDRS_BY_STR.keys():
    if not needed_str in KEYS_BY_STR:
        LOG.error(
            f'Failed to load {needed_str} key pair!'
            f' {needed_str} collateral will not be returned.'
        )

raise SystemExit

### load destination wallet ###

KEYS_DIR=os.path.realpath(ARGS['<keys_dir>'])
PUB = ElectionPublisher(
    role       = 'burner',
    role_index = 1,
    keys_dir   = KEYS_DIR,
    key_name   = ARGS['<key_name>'],
)
LOG.debug(f'PUB: {PUB}')


### create tx to burn and sweep funds ###

MINT_REDEEMER = Redeemer(data=BurnTestTokens())
LOG.debug(f'MINT_REDEEMER: {MINT_REDEEMER}')

CHANNEL_IDS = list(SUB.states.keys())
LOG.debug(f'CHANNEL_IDS: {CHANNEL_IDS}')

BURN_ASSETS = mint_channel_stt_assets(
    SCRIPT.policy_id,
    -1,
    CHANNEL_IDS,
)
LOG.debug(f'BURN_ASSETS: {BURN_ASSETS}')

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
        LOG.debug('\nBurning tokens...')
        BURN_TX = PUB.sign_and_submit_tx(BURN_TXB)
        PUB.wait_for_confirmation(BURN_TX)
        LOG.debug('done')
    except Exception as e:
        LOG.error(e)
        raise
else:
    LOG.error('NOT SURE. ABORT')
