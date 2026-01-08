# Pure functions that construct transactions but don't submit them.

from pycardano import OgmiosV6ChainContext, PaymentSigningKey, Address, PlutusV3Script, TransactionBuilder, TransactionOutput, UTxO, ScriptHash

from .script import PubsubScript
from .types import PubsubAction, PsOpen, PsClose

# Should match config.default.stt_name in aiken.toml
# TODO is there a good way to keep them in sync?
STT_NAME = b"pubsub2-channel-state-token"
 
# usage:
#   mint_fn = channel_nft_minter(script)
#   mint_assets = mint_fn(1)
#   burn_assets = mint_fn(-1)
def channel_nft_minter(policy_id: ScriptHash):
    def channel_nft_assets(n_to_mint: int):
        # the quicker from_primitive way has some normalize error here
        channel_nft = AssetName(STT_NAME)
        asset = Asset()
        asset[channel_nft] = n_to_mint
        assets = MultiAsset()
        assets[policy_id] = asset
        return assets
    return channel_nft_assets

def build_psopen_tx(
    ctx: OgmiosV6ChainContext,
    addr: Address,
    script: PubsubScript,
    oneshot_utxo: UTxO,
):

    action = Redeemer(data=PsOpen())

    mint_fn = channel_nft_minter(script.policy_id)
    assets = mint_fn(1)

    # Lock the NFT at the script address
    # script_addr = Address(payment_part=plutus_script_hash(script), network=Network.TESTNET)
    stt_output = TransactionOutput(
        address=script.address,
        amount=Value(
            2_000_000, # min ADA; adjust as needed
            assets     # the minted NFT
        ),
        # optionally include datum / inline datum here
        # datum=..., or datum_hash=...
    )

    mint_tx = (
        TransactionBuilder(ctx, mint=assets)
        .add_output(stt_output)
        .add_minting_script(script=script.bytes, redeemer=action)
        .add_input(oneshot_utxo)
        .add_input_address(addr)
    )

    return mint_tx
