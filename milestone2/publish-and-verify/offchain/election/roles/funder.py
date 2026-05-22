from election import publisher as ep
from election.plutus import script as eps
from election.plutus import types as ept
from election.plutus.types.channel_id import *
from election.ogmios import OGMIOS_CTX
from election import wallet as ew
from pycardano import UTxO, ScriptHash, MultiAsset, TransactionBuilder, Asset, AssetName
from pathlib import Path
from pycardano import UTxO, OgmiosV6ChainContext
from typing import List

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
        # TODO pass once using more than one: ogmios: OgmiosV6ChainContext,
    ):
        self.keys_dir = keys_dir
        self.publisher = None
        self.subscriber = None
        self.ogmios = OGMIOS_CTX

    def _init_publisher(self, script):
        """Delayed init for publisher because we need to know the one-shot UTxO."""
        self.publisher = ep.ElectionPublisher(
            role="funder",
            index=1,
            keys_dir=self.keys_dir,
            script=script,
            # ogmios=self.ogmios
        )

    def _init_subscriber(self, kupo_args):
        """Delayed init for subscriber because we need to know the args for `kupo --since`."""
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

        init_redeemer = Redeemer(data=et.InitElection())
        assets = mint_channel_stt_assets(script.policy_id, 1)
        state = PubsubState(
            pub_vkh.payload, # TODO is there a cleaner way to get .payload?
            [],
            0
        )

        current_value = Value(
            0, # start with 0, then top up to min below
            assets   # the minted STT
        )

        # Lock the STT at the script address
        stt_output = TransactionOutput(
            address=script.address,
            amount=current_value,
            datum=state
        )

        # top up to min ada
        current_value.coin += min_lovelace(ctx, stt_output)

        # TODO is restating it with new current_value required?
        stt_output = TransactionOutput(
            address=script.address,
            amount=current_value,
            datum=state
        )

        mint_tx = (
            TransactionBuilder(ctx, mint=assets)
            .add_input(oneshot_utxo)
            .add_input_address(pub_addr)
            .add_minting_script(script=script.mint_script, redeemer=mint_redeemer)
            .add_output(stt_output)
        )
        mint_tx.required_signers = [pub_vkh]
        return mint_tx


    def init_election(self, admin, keys_dir=ew.DEF_KEYS_DIR, wallet_name='funder'):
        # TODO will this also generate the keypair if needed? do we want it to?
        funder_addr = load_wallet_addr(keys_dir=keys_dir, name=wallet_name)
        oneshot_utxo = eps.pick_oneshot_utxo(OGMIOS_CTX, funder_addr)
        self.script = ElectionScript(oneshot_utxo)
        self._init_publisher(self.script)
        sub_info = None # TODO write this

        # TODO create and submit tx
        tx = self.build_init_tx()

        return sub_info

    # TODO burn_test_tokens
    # TODO end_election
