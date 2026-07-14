# TODO rename funder -> treasury? maybe later when treasuries involved

from pathlib import Path
from typing import List
from pprint import pformat
from datetime import datetime

from pycardano import *
from ..core import *
# from .admin import *

# careful, admin and pycardano can both shadow this
import logging

LOG = logging.getLogger(__name__)


# TODO where should this live?
def election_json_path(ctx: ElectionContext) -> Path:
	# TODO default dir?
	timestamp = ctx.deployment.deployment_date.strftime("%y%m%d%H%M%S")
	json_path = f'election-{timestamp}.json'
	return json_path


class ObserverNode(ElectionNode):
    """This is the initial and simplest type of ElectionNode.

    Besides observing an election (subscribing + streaming events), it can also:
    1. request an official role from the admin of an existing election
    2. create a new election, either designating an admin or becoming one

    If only observing though, no need for a wallet.
    """

    def __init__(
        self,

        # Observers don't have channels, so they don't officially have an index.
        # But it's still useful for distinguishing state dirs during tests.
        role_index: int,

        # No election context is needed at init time; it's assumed you will
        # create or subscribe to one separately later.

        # If you pass a wallet it'll be used directly. If you pass keys_dir +
        # key_name, a wallet will be generated based on the role_index in the
        # default dir. If you don't pass either you won't have to bother with a
        # wallet, until you want to request/create an official role.
        wallet: Optional[Wallet] = None,
        keys_dir: Optional[Path] = None,
        key_name: Optional[Path] = None,

    ):
        LOG.debug('Observer.__init__')

        # No election here because the Observer has to exist in order to create
        # it. And with no election, the ElectionNode class won't init a
        # subscriber yet either.
        super().__init__(
            role='observer',
            role_index=role_index,
            wallet=wallet,
            script=None,
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

        LOG.debug('Observer._build_init_tx')

        ch_str = self.channel_str()
        tx_msgs = []

        # Without this set, the ObserverNode risks the entire dev wallet when
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
        """Observer sends COLLATERAL_ADA to the admin address. In practice this
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

    def _guard_election(self):
        raise Exception('create or subscribe to an election first')

    def _init_subscriber_from_ctx(self, ctx: ElectionContext):
        """Delayed init for subscriber because we need to know the args for `kupo --since`."""
        LOG.debug('Observer._init_subscriber_from_ctx')
        # if self.election is None:
        #     raise Exception('_init_subscriber_from_ctx should be called as part of init_election')
        # self._guard_election()
        sub_cfg = SubscriberConfig(
            policy_id   = ctx.script.policy_id,
            since_slot  = ctx.deployment.index_from_slot,
            since_block = ctx.deployment.index_from_block_hash,
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
            f'egc:election:{sub_cfg.policy_id}:{sub_cfg.since_slot}:{sub_cfg.since_block}\n'
        )

    def deploy_election(
            self,
            script: ElectionScript,
            init_txb: TransactionBuilder
        ) -> (Transaction, ElectionContext):

        LOG.debug('Observer.deploy_election')

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

        LOG.debug('Observer.init_election')

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
        # self.election = election_ctx
        self.script = election_ctx.script
        json_path = election_json_path(election_ctx)
        election.to_json(json_path)
        LOG.info(f'{self.channel_str()} deployed contract and saved details to {json_path}')
        for msg in tx_msgs:
            LOG.info(msg)

        self._init_subscriber_from_ctx(election_ctx)

        # All the info we really need should be in self.election now;
        # the main reason to return init_tx is so the caller can wait for confirmation.
        return init_tx
