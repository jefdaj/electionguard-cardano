# TODO rename funder -> treasury? maybe later when treasuries involved

# from egc import Election, ElectionPublisher, ElectionSubscriber

# from egc import publisher as ep
# from egc.plutus import script as eps
# from egc.plutus import types as ept
# from egc.plutus.types.channel_id import *
# from egc.ogmios import OGMIOS_CTX, query_network_tip_sync
# from egc import wallet as ew

from pathlib import Path
from typing import List
import logging
from pprint import pformat

LOG = logging.getLogger(__name__)

# import pycardano as pc
# from pycardano import UTxO, ScriptHash, MultiAsset, TransactionBuilder, Asset, AssetName, Redeemer, Value
from pycardano import *

from ..ogmios import *
from ..plutus.oneshot import *
from .admin import Admin
from ..election import ElectionScript

# TODO is there really not a built in convenience function or constant for this?
# TODO where should it live?
LOVELACE_PER_ADA = 1_000_000

# This should match the one defined in aiken.toml
# TODO custom prefix set by funder
STT_PREFIX: str = "egc-election"

def full_stt_name(channel_id: ChannelId) -> bytes:
    id_str = ept.ChannelIdHelper.to_string(channel_id)
    full_str = STT_PREFIX + '-' + id_str + '-stt'
    # return ept.ChannelIdHelper.from_string(full_str)
    return full_str.encode('utf-8')

def top_up_to_min_ada(output):
    """The minimum lovelace for a UTXO depends on the serialized size of the
    output, which includes the coin field itself. In most cases this doesn't
    matter, but in edge cases: A small coin value serializes to fewer bytes than a
    large one.  After you bump coin, the output size could cross a threshold that
    changes the minimum. In practice this rarely causes issues because the min
    lovelace calculation has enough headroom, but if you want to be defensive, you
    can loop until it stabilizes.
    """
    for _ in range(3):  # shouldn't need more than 2 iterations
        min_lv = min_lovelace(OGMIOS_CTX, output)
        new_coin = max(output.amount.coin, min_lv)
        if output.amount.coin == new_coin:
            break
        output.amount.coin = new_coin

# TODO where should this live?
def mint_channel_stt_assets(
        policy_id: ScriptHash,
        n_to_mint: int,
        channel_ids: List[ChannelId]
    ) -> MultiAsset:
    '''Mint or burn (with negative n_to_mint) one or more channel STTs'''
    # the quicker from_primitive way has some normalize error here
    asset = Asset()
    for channel_id in channel_ids:
        stt = AssetName(full_stt_name(channel_id))
        asset[stt] = n_to_mint
    assets = MultiAsset()
    assets[policy_id] = asset
    return assets

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
        self.publisher = self._init_publisher()

        # These need to be delayed because we won't know the deployment details
        # until after init_election().
        self.election = None
        self.subscriber = None

    def _init_publisher(self, script):
        LOG.debug('Funder._init_publisher')
        self.publisher = ElectionPublisher(
            role="funder",
            index=1,
            key_pair=self.key_pair,
            # script=script, TODO not needed, right?
        )

    def _init_subscriber(self, kupo_args):
        """Delayed init for subscriber because we need to know the args for `kupo --since`."""
        LOG.debug('Funder._init_subscriber')
        # TODO write this once publishing works
        # script = ElectionScript(oneshot_utxo)
        # self.subscriber = ElectionSubscriber(self.publisher.script)
        raise NotImplementedError

    def build_init_tx(self, admin: Admin, channel_ada: int) -> TransactionBuilder:
        """Build an InitElection transaction.
        This is an unusual one because it doesn't have any options, so there's
        no point pulling them from static_records.py.
        """

        # TODO merge this into init_election rather than separate builders?

        LOG.debug('Funder.build_init_tx')

        redeemer = Redeemer(data=ept.InitElection())
        LOG.debug('redeemer: %s' % pformat(redeemer))

        admin_id = ChannelIdHelper.from_string('admin')
        assets = mint_channel_stt_assets(self.script.policy_id, 1, [admin_id])
        LOG.debug('assets: %s' % pformat(assets))

        admin_vkh  = admin.publisher.verification_key_hash
        state = ept.channel.AdminChannelState(
            admin       = admin_vkh.payload,
            subchannels = [],
            new_records = [],
            phase       = ept.phase.ElectionConfigPhase(ept.phase.ConfigAnnouncePhase()),
            seq         = 0,
        )
        LOG.debug('state: %s' % pformat(state))

        channel_lovelace = channel_ada * LOVELACE_PER_ADA
        current_value = Value(
            channel_lovelace, # start with the requested amount, then top up below if needed
            assets   # the minted STT
        )
        LOG.debug('current_value before top-up: %s' % pformat(current_value))

        # Lock the STT at the script address
        stt_output = TransactionOutput(
            address=self.script.address,
            amount=current_value,
            datum=state
        )
        LOG.debug('stt_output before top-up: %s' % pformat(stt_output))

        # top up to min ada (warning: mutates in place)
        top_up_to_min_ada(stt_output)
        LOG.debug('current_value after top-up: %s' % pformat(current_value))
        LOG.debug('stt_output after top-up: %s' % pformat(stt_output))

        init_tx = (
            TransactionBuilder(OGMIOS_CTX, mint=assets)
            .add_input(self.script.oneshot_utxo)
            .add_input_address(self.publisher.address)
            .add_minting_script(script=self.script.mint_script, redeemer=redeemer)
            .add_output(stt_output)
        )
        funder_vkh = self.publisher.verification_key_hash
        init_tx.required_signers = [funder_vkh]
        LOG.debug('init_tx:\n%s\n' % pformat(init_tx))

        return init_tx

    # TODO move to oneshot.py
    # def init_script(self):
    #     """Pick oneshot_utxo and parameterize script."""
    #     # Need to load addr separately because self.publisher does not exist yet.
    #     # fund_addr = ew.load_wallet_addr(keys_dir=self.keys_dir, name=self.wallet_name)
    #     # TODO no need to keep a direct reference to script?
    #     fund_addr = self.key_pair.addr
    #     oneshot_utxo = pick_oneshot_utxo(OGMIOS_CTX, fund_addr)
    #     self.script = ElectionScript(oneshot_utxo)

    def init_election(self, admin: Admin, channel_ada: int = 100):
        LOG.debug('Funder.init_election')

        # if self.script is None:
        #     self.init_script()

        # TODO create ElectionScript here

        # TODO move to election.py?
        # Should be done before the first TX is published to ensure everyone indexes it.
        sub_info = query_network_tip_sync()
        LOG.info('sub_info: %s' % pformat(sub_info))

        # Now that we have the Script, we can create the Publisher normally.
        self._init_publisher(self.script)

        # TODO move to election.py?
        init_tx = self.build_init_tx(admin=admin, channel_ada=channel_ada)
        init_tx_submitted = self.publisher.sign_and_submit(init_tx)

        return (sub_info, init_tx_submitted)
