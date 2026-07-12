# TODO rename funder -> treasury? maybe later when treasuries involved

from pathlib import Path
from typing import List
from pprint import pformat
from datetime import datetime

from pycardano import *
from ..core import *
from .admin import *

# careful, admin and pycardano can both shadow this
import logging

LOG = logging.getLogger(__name__)


class FunderNode(ElectionNode):
    """Node to create + fund the Admin, and to recover ADA after the election.
    """

    def __init__(
        self,

        # Expected usage is to create and fund the Funder wallet manually,
        # so no need for Funder to take key_dir + key_name like the other roles.
        wallet: Wallet,

    ):
        LOG.debug('Funder.__init__')

        # No election here because the Funder has to exist in order to create
        # it. And with no election, the ElectionNode class won't init a
        # subscriber yet either.
        super().__init__(
            role='funder',
            role_index=1,
            wallet=wallet,
            election=None,
        )

    def _build_init_tx(
            self,
            script: ElectionScript,
            admin_addr: Address,
            admin_vkh: VerificationKeyHash,
            admin_ada: int
        ) -> Tuple[List[str], TransactionBuilder]:
        """Build an InitElection transaction.
        This is an unusual one because it doesn't have any options, so there's
        no point pulling them from static_records.py.
        """

        LOG.debug('Funder._build_init_tx')

        ch_str = self.channel_str()
        tx_msgs = []

        # Without this set, the FunderNode risks the entire dev wallet when
        # deploying a contract.
        self.publisher.create_own_collateral()
        funder_collateral = self.publisher.wait_for_collateral()

        redeemer = Redeemer(data=InitElection())
        LOG.debug('init redeemer: %s' % pformat(redeemer))

        phase = ElectionConfigPhase(ConfigAnnouncePhase())

        state = AdminChannelState(
            admin       = admin_vkh.payload,
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
            .add_input(script.oneshot_utxo)
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
        """Funder sends COLLATERAL_ADA to the admin address. In practice this
        is usually folded into the admin STT mint tx as an extra output — keep
        this around for tests and for the case where the admin needs a fresh
        collateral mid-election."""
        return self.publisher.send_ada(admin_address, COLLATERAL_LOVELACE)

    def init_script(self):
        """Pick oneshot_utxo and parameterize script."""
        fund_addr = self.publisher.wallet.addr
        oneshot_utxo = pick_oneshot_utxo(OGMIOS_CTX, fund_addr)
        script = ElectionScript.from_oneshot_utxo(oneshot_utxo)
        LOG.debug('script:\n%s\n' % pformat(script))
        return script

    def _init_subscriber(self):
        """Delayed init for subscriber because we need to know the args for `kupo --since`."""
        LOG.debug('Funder._init_subscriber')
        if self.election is None:
            raise Exception('_init_subscriber should be called as part of init_election')
        sub_cfg = SubscriberConfig(
            policy_id   = self.election.script.policy_id,
            since_slot  = self.election.deployment.index_from_slot,
            since_block = self.election.deployment.index_from_block_hash,
        )
        self.subscriber = ElectionSubscriber(
            config      = sub_cfg,
            on_action   = lambda x: None,
            on_rollback = lambda x: None,
        )
        self.subscriber.start()
        LOG.info(f'Subscribe to this election with:\n\n{pformat(sub_cfg)}\n')
        LOG.debug(
            f'Or for dev debugging:\n\n'
            f'./subscribe.py {sub_cfg.policy_id} {sub_cfg.since_slot} {sub_cfg.since_block}\n'
        )

    def deploy_election(
            self,
            script: ElectionScript,
            init_txb: TransactionBuilder
        ) -> (Transaction, ElectionContext):

        LOG.debug('Funder.deploy_election')

        tip = query_network_tip_sync()
        LOG.debug('tip before init_tx submitted: %s' % pformat(tip))

        init_tx = self.publisher.sign_and_submit_tx(init_txb)

        deployment = ElectionDeployment(
            network               = Network.TESTNET,
            funder_address        = self.publisher.wallet.addr,
            deployment_date       = datetime.now(), # TODO get now() before sign_and_submit_tx?
            index_from_slot       = tip['slot'],
            index_from_block_hash = tip['block_hash'],
        )
        LOG.debug('deployment: %s' % pformat(deployment))

        election_ctx = ElectionContext(script=script, deployment=deployment)
        LOG.debug('election_ctx: %s' % pformat(election_ctx))

        return (init_tx, election_ctx)

    def init_election(
            self,
            script: ElectionScript,
            admin_addr: Address,
            admin_vkh: VerificationKeyHash,
            admin_ada: int = 100
        ) -> Transaction:

        LOG.debug('Funder.init_election')

        (tx_msgs, init_txb) = self._build_init_tx(
            script     = script,
            admin_addr = admin_addr,
            admin_vkh  = admin_vkh,
            admin_ada  = admin_ada
        )
        (init_tx, election_ctx) = self.deploy_election(script, init_txb)

        # TODO come up with a better default path here
        # timestamp = election_ctx.deployment.deployment_date.strftime("%y%m%d%H%M%S")
        # json_path = f'election-{timestamp}.json'
        self.election = election_ctx
        json_path = self.election_json_path()
        self.election.to_json(json_path)
        LOG.info(f'{self.channel_str()} deployed contract and saved details to {json_path}')
        for msg in tx_msgs:
            LOG.info(msg)

        self._init_subscriber()

        # All the info we really need should be in self.election now;
        # the main reason to return init_tx is so the caller can wait for confirmation.
        return init_tx

    def election_json_path(self) -> Optional[Path]:
        # TODO default dir?
        if self.election is None:
            return None
        timestamp = self.election.deployment.deployment_date.strftime("%y%m%d%H%M%S")
        json_path = f'election-{timestamp}.json'
        return json_path

    def _build_burn_tx(self) -> Tuple[List[str], TransactionBuilder]:

        # Without this set, the FunderNode risks the entire dev wallet when
        # deploying a contract.
        self.publisher.create_own_collateral()
        funder_collateral = self.publisher.wait_for_collateral()

        # Messages to log if/when the TX succeeds
        ch_str = self.channel_str()
        tx_msgs = []

        mint_redeemer = Redeemer(data=BurnTestTokens())
        LOG.debug(f'mint_redeemer: {mint_redeemer}')

        # TODO why is this failing? seems to not get the message that STTs have been burned?
        channel_ids = self.subscriber.current_channel_ids()
        LOG.debug(f'channel_ids: {channel_ids}')

        if len(channel_ids) == 0:
            # shouldn't normally happen
            LOG.debug(f'subscriber history:\n{pformat(self.subscriber._history)}')
            msg = 'skip burn tx because no channels to burn'
            LOG.error(msg)
            raise RuntimeError(msg)

        burn_assets = mint_channel_stt_assets(
            self.election.script.policy_id,
            -1,
            channel_ids,
        )
        LOG.debug(f'burn_assets: {burn_assets}')

        burn_txb = (
            TransactionBuilder(OGMIOS_CTX, mint=burn_assets)
            .add_minting_script(script=self.election.script.mint_script, redeemer=mint_redeemer)
        )

        burn_txb.collaterals.append(funder_collateral)

        for channel_id in channel_ids:
            ch_str = channel_id_to_string(channel_id)
            utxo = self.subscriber.current_utxo(channel_id)
            LOG.debug(f'{ch_str} STT UTXO to spend: {utxo}')
            spend_redeemer = Redeemer(data=BurnTestTokens())
            burn_txb = burn_txb.add_script_input(
                utxo,
                script=self.election.script.spend_script,
                redeemer=spend_redeemer
            )
            tx_msgs.append(f'{ch_str} burned {ch_str} channel STT and recovered fee pool ADA.')

        LOG.debug('burn_txb:\n%s\n' % pformat(burn_txb))

        return (tx_msgs, burn_txb)

    def burn_test_tokens(self):
        """Clean up test tokens.

        WARNING: The on-chain code lets anyone do this, not just the funder.
        BurnTestTokens should be removed before production use.
        """
        if not IS_TEST:
            err = 'burn_test_tokens is only for test mode'
            LOG.error(err)
            raise RuntimeError(err)
        if self.election is None:
            raise Exception('init_election must be called before burn_test_tokens')
        if self.subscriber is None:
            raise Exception('init_subscriber must be called before burn_test_tokens')
        (tx_msgs, burn_txb) = self._build_burn_tx()
        burn_tx  = self.publisher.sign_and_submit_tx(burn_txb)
        json_path = self.election_json_path()
        for msg in tx_msgs:
            LOG.info(msg)
        ch_str = self.channel_str()
        LOG.info(f'{ch_str} burned all test tokens and recovered fee pool ADA from {json_path}')
        return burn_tx

    def recover_all_collateral(self, keys_dir: Path) -> Transaction:
        if not IS_TEST:
            err = 'recover_all_collateral is only for test mode'
            LOG.error(err)
            raise RuntimeError(err)
        ch_str = self.channel_str()
        errors = []
        last_tx = None # only have to wait once

        for channel_id in self.subscriber.all_channel_ids():

            # Can't use the current state because the channel may be closed.
            # But it should have either an input or output at least.
            with self.subscriber._history_lock:
                event = self.subscriber._history[channel_id][-1]
                if event.output_state:
                    state = event.output_state
                else:
                    state = event.input_state

            try:
                LOG.debug(f'state: {state}')
                pub_addr   = publisher_address(state)
                LOG.debug(f'pub_addr: {pub_addr}')
                (sk_path, pub_wallet) = load_wallet_by_address(pub_addr, keys_dir=keys_dir)
                LOG.debug(f'sk_path: {sk_path}')
                LOG.debug(f'pub_wallet: {pub_wallet}')
                tx = self.publisher.return_collateral(
                    self.publisher.wallet.addr,
                    from_wallet = pub_wallet,
                )
                if tx is not None:
                    last_tx = tx
                    LOG.info(f'{ch_str} recovered collateral from {sk_path}')
                else:
                    LOG.info(f'{ch_str} has no collateral UTXO. Already returned?')
            except Exception as e:
                LOG.exception(f'{ch_str} failed to recover collateral from {pub_addr}')
                errors.append(e)
        if errors:
            raise ExceptionGroup('recover_all_collateral had failures', errors)
        return last_tx
