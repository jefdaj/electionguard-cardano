# Pure functions that construct transactions but don't submit them.

from pycardano import *
from typing import List

from .script import PubsubScript
from .types import PubsubAction, PsOpen, PsPublish, PsClose, PubsubState, CIDv1

# Should match config.default.stt_name in aiken.toml
# TODO is there a good way to keep them in sync?
STT_NAME = b"pubsub3-channel-stt"

def mint_channel_stt_assets(policy_id: ScriptHash, n_to_mint: int) -> MultiAsset:
    # the quicker from_primitive way has some normalize error here
    channel_stt = AssetName(STT_NAME)
    asset = Asset()
    asset[channel_stt] = n_to_mint
    assets = MultiAsset()
    assets[policy_id] = asset
    return assets

# TODO add option for how many publish TXs to fund initially?
def build_psopen_tx(
    ctx: OgmiosV6ChainContext,
    pub_addr: Address,
    pub_vkh: VerificationKeyHash,
    script: PubsubScript,
    oneshot_utxo: UTxO,
) -> TransactionBuilder:

    mint_redeemer = Redeemer(data=PsOpen())
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
) -> TransactionBuilder:

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

def build_pspublish_tx(
    ctx: OgmiosV6ChainContext,
    script: PubsubScript,
    pub_addr: Address,
    pub_vkh: VerificationKeyHash,
    cids: List[CIDv1]
) -> TransactionBuilder:

    state_utxo = find_channel_stt_utxo(ctx, script.policy_id)
    spend_redeemer = Redeemer(data=PsPublish())

    # TODO remove
    # print(f"Amount type: {type(state_utxo.output.amount)}")
    # print(f"Amount value: {state_utxo.output.amount}")
    # print(f"Amount coin: {state_utxo.output.amount.coin}")
    # print(f"Amount multi_asset: {state_utxo.output.amount.multi_asset}")

    old_state = PubsubState.from_cbor(state_utxo.output.datum.cbor)
    new_state = PubsubState(
        pub_vkh.payload,
        cids,
        old_state.seq + 1
    )

    # We need the old_value unmutated because PyCardano will use it to calculate the inputs,
    # so create a separate new_value to top up.
    old_value = state_utxo.output.amount
    new_value = Value.from_primitive(old_value.to_primitive())  # deep copy

    # only used for calculating required_min_ada below
    tmp_output = TransactionOutput(
        address=script.address,
        amount=old_value,
        datum=new_state
    )

    # top up with ADA as needed
    required_min_ada = min_lovelace(ctx, tmp_output)
    old_ada = int(old_value.coin)
    if old_ada < required_min_ada:
        delta = required_min_ada - old_ada
        new_value.coin = old_value.coin + delta

    stt_output = TransactionOutput(
        address=script.address,
        amount=new_value,
        datum=new_state
    )

    print(f"Script address from Python: {script.address}")
    print(f"Input UTxO address: {state_utxo.output.address}")
    print(f"Output address: {stt_output.address}")

    pub_tx = (
        TransactionBuilder(ctx)
        .add_script_input(state_utxo, script=script.spend_script, redeemer=spend_redeemer)
        .add_input_address(pub_addr) # so far, fees come from publisher wallet here
        .add_output(stt_output)
    )
    pub_tx.required_signers = [pub_vkh]
    return pub_tx

def build_psclose_tx(
    ctx: OgmiosV6ChainContext,
    pub_addr: Address,
    pub_vkh: VerificationKeyHash,
    script: PubsubScript
) -> TransactionBuilder:

    # These must be separate because pycardano will tag them each with a purpose (mint or spend)
    mint_redeemer  = Redeemer(data=PsClose())
    spend_redeemer = Redeemer(data=PsClose())

    assets = mint_channel_stt_assets(script.policy_id, -1)
    state_utxo = find_channel_stt_utxo(ctx, script.policy_id)

    burn_tx = (
        TransactionBuilder(ctx, mint=assets)
        .add_minting_script(script=script.mint_script, redeemer=mint_redeemer)
        .add_script_input(state_utxo, script=script.spend_script, redeemer=spend_redeemer)
        .add_input_address(pub_addr)
    )
    burn_tx.required_signers = [pub_vkh] # TODO is this needed?
    return burn_tx
