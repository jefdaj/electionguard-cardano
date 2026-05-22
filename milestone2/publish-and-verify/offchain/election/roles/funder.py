from election import publisher as ep
from election.plutus import script as eps
from election.plutus import types as ept
from election.plutus.types.channel_id import *
from election.ogmios import OGMIOS_CTX
from election import wallet as ew
# import pycardano as pc
# from pycardano import UTxO, ScriptHash, MultiAsset, TransactionBuilder, Asset, AssetName, Redeemer, Value
from pycardano import *
from pathlib import Path
# from pycardano import UTxO, OgmiosV6ChainContext
from typing import List
import logging
from pprint import pformat

log = logging.getLogger(__name__)

# This should match the one defined in aiken.toml
# TODO get them from a common source?
STT_PREFIX: str = "egc-election"

def full_stt_name(channel_id: ChannelId) -> bytes:
    id_str = ept.ChannelIdHelper.to_string(channel_id)
    full_str = STT_PREFIX + '-' + id_str + '-stt'
    # return ept.ChannelIdHelper.from_string(full_str)
    return full_str.encode('utf-8')

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
    Note that unlike other roles, this one has no built-in generate_keys functionality.
    """

    def __init__(
        self,
        keys_dir: Path,
        wallet_name: str,
        # TODO pass once using more than one: ogmios: OgmiosV6ChainContext,
    ):
        log.debug('Funder.__init__')
        self.keys_dir = keys_dir
        self.wallet_name = wallet_name # TODO rename key_name?
        self.publisher = None
        self.subscriber = None
        self.ogmios = OGMIOS_CTX

    def _init_publisher(self, script):
        """Delayed init for publisher because we need to know the one-shot UTxO."""
        log.debug('Funder._init_publisher')
        self.publisher = ep.ElectionPublisher(
            role="funder",
            index=1,
            keys_dir=self.keys_dir,
            script=script,
            key_name=self.wallet_name,
            # ogmios=self.ogmios
        )

    def _init_subscriber(self, kupo_args):
        """Delayed init for subscriber because we need to know the args for `kupo --since`."""
        log.debug('Funder._init_subscriber')
        # TODO write this once publishing works
        # script = ElectionScript(oneshot_utxo)
        self.subscriber = eps.Subscriber(self.publisher.script)

    def build_init_tx(
        self,
        # ctx: OgmiosV6ChainContext,
        # pub_addr: Address,
        # pub_vkh: VerificationKeyHash,
        # script: PubsubScript,
        # oneshot_utxo: UTxO,
    ) -> TransactionBuilder:
        log.debug('Funder.build_init_tx')

        init_redeemer = Redeemer(data=ept.InitElection())
        log.debug('redeemer: %s' % pformat(init_redeemer))

        admin_id = ChannelIdHelper.from_string('admin')
        assets = mint_channel_stt_assets(self.script.policy_id, 1, [admin_id])
        log.debug('assets: %s' % pformat(assets))

        vkh = self.publisher.verification_key_hash
        state = ept.channel.AdminChannelState(
            admin       = vkh.payload,
            subchannels = [],
            new_records = [],
            phase       = ept.phase.ElectionConfigPhase(ept.phase.ConfigAnnouncePhase()),
            seq         = 0,
        )
        log.debug('state: %s' % pformat(state))

        current_value = Value(
            0, # start with 0, then top up to min below
            assets   # the minted STT
        )
        log.debug('current_value before top-up: %s' % pformat(current_value))

        # Lock the STT at the script address
        stt_output = TransactionOutput(
            address=self.script.address,
            amount=current_value,
            datum=state
        )
        log.debug('stt_output before top-up: %s' % pformat(stt_output))

        # top up to min ada
        current_value.coin += min_lovelace(self.ogmios, stt_output)
        log.debug('current_value after top-up: %s' % pformat(current_value))

        # TODO is restating it with new current_value required?
        # stt_output = TransactionOutput(
            # address=self.script.address,
            # amount=current_value,
            # datum=state
        # )
        log.debug('stt_output after top-up: %s' % pformat(stt_output))

        # TODO is init_redeemer what we need here? or a separate one?
        mint_tx = (
            TransactionBuilder(self.ogmios, mint=assets)
            .add_input(self.script.oneshot_utxo)
            .add_input_address(self.publisher.address)
            .add_minting_script(script=self.script.mint_script, redeemer=init_redeemer)
            .add_output(stt_output)
        )
        mint_tx.required_signers = [vkh]
        log.debug('mint_tx:\n%s\n' % pformat(mint_tx))

        return mint_tx


    def init_election(self, admin):
        log.debug('Funder.init_election')
        # TODO will this also generate the keypair if needed? do we want it to?
        funder_addr = ew.load_wallet_addr(keys_dir=self.keys_dir, name=self.wallet_name)
        oneshot_utxo = eps.pick_oneshot_utxo(OGMIOS_CTX, funder_addr)
        self.script = eps.ElectionScript(oneshot_utxo)
        self._init_publisher(self.script)
        sub_info = None # TODO write this

        # TODO create and submit tx
        tx = self.build_init_tx()

        return sub_info

    # TODO burn_test_tokens
    # TODO end_election
