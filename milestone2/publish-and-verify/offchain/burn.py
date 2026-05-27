#!/usr/bin/env python3

'''Usage:
  ./burn.py <slot> <block_hash> <policy_id> <dest_addr>
'''

import logging
import os
import time
from pprint import pformat
from docopt import docopt
from pycardano import Redeemer, ScriptHash, Address
from election.plutus import types as ept
from election.plutus.types.channel import ADMIN_CHANNEL_ID
from election import subscriber as es
from election.roles.funder import mint_channel_stt_assets

logging.basicConfig(
  encoding='utf-8',
  level=logging.DEBUG,
  format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

# TODO consistent variable name casing

LOG = logging.getLogger(os.path.basename(__file__))

args = docopt(__doc__)


### subscribe to find latest utxos ###

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

LOG.info(f'final utxos: {pformat(sub.utxos)}')

### create tx to burn and sweep funds ###

redeemer = Redeemer(data=ept.BurnTestTokens())
LOG.debug(f'redeemer: {redeemer}')

channel_ids = list(sub.states.keys())
LOG.info(f'channel_ids: {channel_ids}')

burn_assets = mint_channel_stt_assets(
    ScriptHash(bytes.fromhex(args['<policy_id>'])),
    -1,
    channel_ids,
)
LOG.info(f'burn_assets: {burn_assets}')

dest_addr = Address.decode(args['<dest_addr>'])
LOG.info(f'dest_addr: {dest_addr}')

# TODO dest_output


# burn_tx = (
    # TransactionBuilder(OGMIOS_CTX, mint=assets)
    # .add_input(self.script.oneshot_utxo)
    # .add_minting_script(script=self.script.mint_script, redeemer=redeemer)
    # .add_output(dest_output)
# )
# LOG.debug('burn_tx:\n%s\n' % pformat(burn_tx))


