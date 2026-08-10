from pathlib import Path
from typing import List
from pprint import pformat
from datetime import datetime

from pycardano import *
from ..core import *
from .observer import ObserverNode

import logging
LOG = logging.getLogger(__name__)


# TODO where should this live?
def election_json_path(ctx: ElectionContext) -> Path:
	# TODO default dir?
    # timestamp = ctx.deployment.deployment_date.strftime("%y%m%d%H%M%S")
	json_path = f'election-{ctx.deployment.since_slot}.json'
	return json_path


# TODO does it matter whether funder is actually a subclass of observer?
class FunderNode(ObserverNode):
    """The funder creates an election and contributes funds for TX fees, then
    hands control to an admin. The funder doesn't have any special abilities
    after that, except that there's an expectation (not enforced on chain) that
    election officials will return any remaining channel funds + collateral
    UTXOs to the funder after the election.

    Sometimes the admin and funder nodes are run by the same person. In that
    case the funder can be created temporarily by the admin just to do the
    init_election step."""

    def __init__(
        self,

        # Where to keep records_to_post, records_fetched, and other files as needed.
        private_dir: Path,

        # For now, we assume a funder starts with an already generated and
        # funded dev wallet.
        wallet: Wallet,
    ):
        LOG.debug('Funder.__init__')
        # No election here because it doesn't exist yet. And with no election,
        # the ElectionNode class won't init a subscriber yet either.
        super().__init__(
            private_dir=private_dir,
            role='funder',
            role_index=1,
            wallet=wallet,
        )

    def _build_init_tx(
            self,
            script: ElectionScript,
            oneshot_utxo: UTxO,
            admin_addr: Address,
            admin_vkh: VerificationKeyHash,
            admin_ada: int
        ) -> Tuple[List[str], TransactionBuilder]:
        "Build an InitElection transaction."
        LOG.debug('Funder._build_init_tx')

        ch_str = self.channel_str()
        tx_msgs = []

        # Without this set, the FunderNode risks the entire dev wallet when
        # deploying a contract.
        self.publisher.create_own_collateral()
        funder_collateral = self.publisher.await_collateral()

        redeemer = Redeemer(data=InitElection())
        LOG.debug('init redeemer: %s' % pformat(redeemer))

        phase = ElectionConfigPhase(ConfigAnnouncePhase())

        state = AdminChannelState(
            admin       = admin_vkh.payload,
            ipfs_node   = None,
            subchannels = [],
            new_records = [],
            phase       = phase,
            seq         = 0,
        )
        LOG.debug('init state: %s' % pformat(state))
        assert isinstance(state, AdminChannelState)

        datum: ChannelState = AdminChannel(state=state)
        LOG.debug('init datum: %s' % pformat(datum))
        assert isinstance(datum, ChannelState)

        assets = mint_channel_stt_assets(script.policy_id, 1, [ADMIN_CHANNEL_ID])
        LOG.debug('init assets: %s' % pformat(assets))

        # TODO no need to top up! just don't allow admin_ada < some reasonable minimum like 5 or 10
        # TODO constant for the amount below which you should get a warning to top up a channel
        # TODO and that should probably also be the minimum, or the minimum is larger at least
        admin_stt_amount = Value(admin_ada * LOVELACE_PER_ADA, assets)
        LOG.debug('admin_stt_amount: %s' % pformat(admin_stt_amount))

        # TODO what needs updating here? just the comment?
        # Normally we get the addr via self.election.address,
        # but that won't exist until after init_election.
        script_addr = Address(script.policy_id, network=Network.TESTNET)
        LOG.debug(f'script_addr: {script_addr}')

        # Lock the STT at the script address along with the initial state datum
        admin_stt_output = TransactionOutput(
            address=script_addr,
            amount=admin_stt_amount,
            datum=datum,
        )
        LOG.debug('init admin_stt_output: %s' % pformat(admin_stt_output))

        # Collateral so the admin can interact with the contract.
        admin_collateral = TransactionOutput(
            address = admin_addr,
            amount = Value(coin=COLLATERAL_LOVELACE),
        )
        LOG.debug('init admin_collateral: %s' % pformat(admin_collateral))

        txb = (
            TransactionBuilder(OGMIOS_CTX, mint=assets)
            .add_input(oneshot_utxo)
            .add_input_address(self.publisher.wallet.addr)
            .add_minting_script(script=script.mint_script, redeemer=redeemer)
            .add_output(admin_stt_output)
            .add_output(admin_collateral)
        )
        txb.collaterals.append(funder_collateral)
        txb.required_signers = [self.publisher.wallet.vkh]
        LOG.debug('init txb:\n%s\n' % pformat(txb))

        tx_msgs.append(f'{ch_str} set initial phase to {phase}')
        tx_msgs.append(f'{ch_str} minted admin channel STT and locked {admin_ada} ADA with it to pay fees.')
        tx_msgs.append(f'{ch_str} sent 5 ADA to admin for use as collateral.')

        return (tx_msgs, txb)

    # TODO remove?
    def fund_admin_collateral(
        admin_address: Address,
    ) -> Transaction:
        """Observer sends COLLATERAL_ADA to the admin address. In practice this
        is usually folded into the admin STT mint tx as an extra output — keep
        this around for tests and for the case where the admin needs a fresh
        collateral mid-election."""
        return self.publisher.send_ada(admin_address, COLLATERAL_LOVELACE)

    # TODO merge into init_election? maybe if no script passed to it?
#     def init_script(self):
#         """Pick oneshot_utxo and parameterize script."""
#         fund_addr = self.publisher.wallet.addr
#         oneshot_utxo = pick_oneshot_utxo(OGMIOS_CTX, fund_addr)
#         script = ElectionScript.from_oneshot_utxo(oneshot_utxo)
#         LOG.debug('script:\n%s\n' % pformat(script))
#         return script

    def _guard_election(self):
        raise Exception('create or subscribe to an election first')

    def deploy_election(
            self,
            script: ElectionScript,
            init_txb: TransactionBuilder
        ) -> tuple[Transaction, ElectionContext]:

        LOG.debug('Funder.deploy_election')

        tip = query_network_tip_sync()
        LOG.debug('tip before init_tx submitted: %s' % pformat(tip))

        init_tx = self.publisher.sign_and_submit_tx(init_txb)

        deployment = ElectionDeployment(
            funder_address = self.publisher.wallet.addr,
            since_slot     = tip['slot'],
            since_block    = tip['block_hash'],
            network_magic  = DEFAULT_NETWORK_MAGIC, # TODO dynamic
        )
        LOG.debug('deployment: %s' % pformat(deployment))

        election_ctx = ElectionContext(script=script, deployment=deployment)
        LOG.debug('election_ctx: %s' % pformat(election_ctx))

        return (init_tx, election_ctx)

    def init_election(
            self,
            # script: ElectionScript,
            # admin_addr: Address = None, # TODO remove?
            admin_vkh: VerificationKeyHash = None,
            admin_ada: int = 100,
            oneshot_utxo: UTxO = None, # Leave off to auto-pick from funder wallet
            # funder_wallet: Wallet = None,
            subscribe = True, # set False only when the FunderNode is temporary
            context_backup_json: Optional[Path] = None,
        ) -> tuple[Transaction, ElectionConfig]:

        LOG.debug('Funder.init_election')

        if admin_vkh is None:
            admin_vkh = self.publisher.wallet.vkh

        # for sending collateral
        admin_addr = addr_for_vkh(admin_vkh) # TODO dynamic network

        # TODO remove if always calling from FunderNode
        # if oneshot_utxo is not None:
        #     assert funder_wallet is None, "passed both oneshot_utxo and funder_wallet"
        # else:
        #     if funder_wallet is None:
        #         funder_wallet = self.publisher.wallet
        #     oneshot_utxo = pick_oneshot_utxo(OGMIOS_CTX, funder_wallet.addr)

        funder_wallet = self.publisher.wallet
        oneshot_utxo = pick_oneshot_utxo(OGMIOS_CTX, funder_wallet.addr)

        script = derive_script(oneshot_utxo)

        (tx_msgs, init_txb) = self._build_init_tx(
            script       = script,
            oneshot_utxo = oneshot_utxo,
            admin_addr   = admin_addr,
            admin_vkh    = admin_vkh,
            admin_ada    = admin_ada
        )
        for msg in tx_msgs:
            LOG.info(msg)

        (init_tx, election_ctx) = self.deploy_election(script, init_txb)
        LOG.info(f'{self.channel_str()} deployed contract')

        if context_backup_json is not None:
            election_ctx.to_json(context_backup_json)
            LOG.info(f'{self.channel_str()} saved contract details to {context_backup_json}')

        election_cfg = ElectionConfig.from_election_context(election_ctx)
        if subscribe:
            self.subscribe(election_cfg)

        LOG.info(f'Subscribe to this election with:\n\n{election_cfg.to_qr_str()}\n')

        return (init_tx, election_cfg)
