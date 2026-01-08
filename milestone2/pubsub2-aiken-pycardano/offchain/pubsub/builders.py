# Pure functions that construct transactions but don't submit them.

from pycardano import *

from .script import PubsubScript
from .types import PubsubAction, PsOpen, PsClose

# Should match config.default.stt_name in aiken.toml
# TODO is there a good way to keep them in sync?
STT_NAME = b"pubsub2-channel-state-token"

# TODO get this from somewhere official?
MIN_ADA = 2_000_000
 
def mint_channel_stt_assets(policy_id: ScriptHash, n_to_mint: int):
    # the quicker from_primitive way has some normalize error here
    channel_stt = AssetName(STT_NAME)
    asset = Asset()
    asset[channel_stt] = n_to_mint
    assets = MultiAsset()
    assets[policy_id] = asset
    return assets

def build_psopen_tx(
    ctx: OgmiosV6ChainContext,
    addr: Address,
    script: PubsubScript,
    oneshot_utxo: UTxO,
):
    action = Redeemer(data=PsOpen())
    assets = mint_channel_stt_assets(script.policy_id, 1)
    # Lock the STT at the script address
    # script_addr = Address(payment_part=plutus_script_hash(script), network=Network.TESTNET)
    stt_output = TransactionOutput(
        address=script.address,
        amount=Value(
            MIN_ADA, # TODO add more for future txs?
            assets   # the minted STT
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

def utxo_contains_channel_stt(
    policy_id: str,
    utxo: TransactionOutput
) -> bool:
    name = AssetName(STT_NAME)
    try:
        return utxo.output.amount.multi_asset[policy_id].get(name, 0) == 1
    except Exception as e:
        # print('error:', str(e))
        return False

def find_channel_stt_utxo(
    ctx: OgmiosV6ChainContext,
    policy_id: ScriptHash,
):
    script_addr = Address(payment_part=policy_id, network=Network.TESTNET)
    matches = list(
        u for u in ctx.utxos(script_addr)
        if utxo_contains_channel_stt(policy_id, u)
    )
    if len(matches) == 0:
        print('no state utxo found')
        return None
    elif len(matches) > 1:
        raise Exception(f'found multiple state utxos: {matches}')
    else:
        return matches[0]

def build_psclose_tx(
    ctx: OgmiosV6ChainContext,
    addr: Address,
    script: PubsubScript
):
    action = Redeemer(data=PsClose())
    assets = mint_channel_stt_assets(script.policy_id, -1)
    state_utxo = find_channel_stt_utxo(ctx, script.policy_id)
    burn_tx = (
        TransactionBuilder(ctx, mint=assets)
        .add_minting_script(script=script.bytes, redeemer=action)
        .add_input(state_utxo)
        .add_input_address(addr)
    )
    return burn_tx
