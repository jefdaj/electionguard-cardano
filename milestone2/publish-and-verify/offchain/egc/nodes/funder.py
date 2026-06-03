# TODO rename funder -> treasury? maybe later when treasuries involved

# from egc import Election, ElectionPublisher, ElectionSubscriber

# from egc import publisher as ep
# from egc.plutus import script as eps
# from egc.plutus import types as ept
# from egc.ogmios import OGMIOS_CTX, query_network_tip_sync

from pycardano import *
import logging

LOG = logging.getLogger(__name__)

from pathlib import Path
from typing import List
from pprint import pformat
from datetime import datetime

# import pycardano as pc
# from pycardano import UTxO, ScriptHash, MultiAsset, TransactionBuilder, Asset, AssetName, Redeemer, Value

# from egc import *
from ..core import *
from .admin import *

class Funder:
    """Wallet to create + fund the Admin, and to recover ADA after the election.
    """

    def __init__(
        self,

        # Expected usage is to create and fund the Funder wallet manually,
        # so no need for Funder to take key_dir + key_name like the other roles.
        key_pair: KeyPair,

    ):
        LOG.debug('Funder.__init__')
        self.key_pair = key_pair
        self._init_publisher()

        # These need to be delayed because we won't know the deployment details
        # until after init_election().
        self.election = None
        self.subscriber = None

    def _init_publisher(self):
        LOG.debug('Funder._init_publisher')
        self.publisher = ElectionPublisher(
            role="funder",
            role_index=1,
            key_pair=self.key_pair,
            # script=script, TODO not needed, right?
        )

    def build_init_tx(self, script: ElectionScript, admin_vkh: VerificationKeyHash, admin_ada: int) -> TransactionBuilder:
        """Build an InitElection transaction.
        This is an unusual one because it doesn't have any options, so there's
        no point pulling them from static_records.py.
        """

        LOG.debug('Funder.build_init_tx')

        redeemer = Redeemer(data=InitElection())
        LOG.debug('redeemer: %s' % pformat(redeemer))

        assets = mint_channel_stt_assets(script.policy_id, 1, [ADMIN_CHANNEL_ID])
        LOG.debug('assets: %s' % pformat(assets))

        # admin_vkh  = admin.publisher.verification_key_hash
        state = AdminChannelState(
            admin       = admin_vkh.payload,
            subchannels = [],
            new_records = [],
            phase       = ElectionConfigPhase(ConfigAnnouncePhase()),
            seq         = 0,
        )
        LOG.debug('state: %s' % pformat(state))

        channel_lovelace = admin_ada * LOVELACE_PER_ADA
        current_value = Value(
            channel_lovelace, # start with the requested amount, then top up below if needed
            assets   # the minted STT
        )
        LOG.debug('current_value before top-up: %s' % pformat(current_value))

        script_addr = Address(script.policy_id, network=Network.TESTNET)
        LOG.debug(f'script_addr: {script_addr}')

        # Lock the STT at the script address
        stt_output = TransactionOutput(
            address=script_addr,
            amount=current_value,
            datum=state
        )
        LOG.debug('stt_output before top-up: %s' % pformat(stt_output))

        # top up to min ada (warning: mutates in place)
        top_up_to_min_ada(stt_output)
        LOG.debug('current_value after top-up: %s' % pformat(current_value))
        LOG.debug('stt_output after top-up: %s' % pformat(stt_output))

        init_txb = (
            TransactionBuilder(OGMIOS_CTX, mint=assets)
            .add_input(script.oneshot_utxo)
            .add_input_address(self.publisher.key_pair.addr)
            .add_minting_script(script=script.mint_script, redeemer=redeemer)
            .add_output(stt_output)
        )
        # funder_vkh = self.publisher.verification_key_hash
        init_txb.required_signers = [self.key_pair.vkh]
        LOG.debug('init_txb:\n%s\n' % pformat(init_txb))

        return init_txb

    def init_script(self):
        """Pick oneshot_utxo and parameterize script."""
        fund_addr = self.key_pair.addr
        oneshot_utxo = pick_oneshot_utxo(OGMIOS_CTX, fund_addr)
        script = ElectionScript.from_oneshot_utxo(oneshot_utxo)
        LOG.debug('script:\n%s\n' % pformat(script))
        return script

    def deploy_election(
            self,
            script: ElectionScript,
            init_txb: TransactionBuilder
        ) -> (Transaction, ElectionContext):

        LOG.debug('Funder.deploy_election')

        tip = query_network_tip_sync()
        LOG.debug('tip before init_tx submitted: %s' % pformat(tip))

        init_tx = self.publisher.sign_and_submit(init_txb)

        deployment = ElectionDeployment(
            network               = Network.TESTNET,
            funder_address        = self.key_pair.addr,
            deployment_date       = datetime.now(), # TODO get now() before sign_and_submit?  index_from_slot       = tip['slot'],
            index_from_block_hash = tip['block_hash'],
        )
        LOG.debug('deployment: %s' % pformat(deployment))

        election_ctx = ElectionContext(script=script, deployment=deployment)
        LOG.debug('election_ctx: %s' % pformat(election_ctx))

        raise SystemExit
        return (init_tx, election_ctx)

    def init_election(
            self,
            script: ElectionScript,
            admin_vkh: VerificationKeyHash,
            admin_ada: int = 100
        ) -> (Transaction, ElectionContext):

        LOG.debug('Funder.init_election')

        init_txb = self.build_init_tx(script=script, admin_vkh=admin_vkh, admin_ada=admin_ada)
        (init_tx, election_ctx) = self.deploy_election(script, init_txb)

        # TODO come up with a better default path here
        timestamp = datetime.fromisoformat(election_ctx.deployment.deployment_date).strftime("%y%m%d%H%M%S")
        election_ctx.to_json(f'election-{timestamp}.json')

        # All the info we really need should be in election_ctx now;
        # the main reason to return init_tx is so the caller can wait for confirmation.
        return (init_tx, election_ctx)

    def _init_subscriber(self, kupo_args):
        """Delayed init for subscriber because we need to know the args for `kupo --since`."""
        LOG.debug('Funder._init_subscriber')
        # TODO write this once publishing works
        # script = ElectionScript(oneshot_utxo)
        # self.subscriber = ElectionSubscriber(self.publisher.script)
        raise NotImplementedError
