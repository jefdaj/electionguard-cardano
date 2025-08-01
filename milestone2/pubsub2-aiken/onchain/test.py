#!/usr/bin/env python3

import cbor2
import json
import os
import subprocess
import tempfile
import time

from dataclasses import dataclass
from typing import List

from pycardano import *
from pycardano.hash import (
    VerificationKeyHash,
    TransactionId,
    ScriptHash,
)

# This is a temporary hack for use with `aiken blueprint apply`
# See https://github.com/Python-Cardano/pycardano/issues/439
# TODO revisit once native apply_params support is released
@dataclass
class OutputReferenceHack(PlutusData):
    CONSTR_ID = 0
    transaction_id: bytes
    index: int

def pick_oneshot_utxo(context, addr):
    # No particular logic to max here; any UTXO should work for the initial tests
    utxos = context.utxos(addr)
    if not utxos:
        raise Exception(f'addr {addr} has no UTXOs')
    utxo = max(utxos, key=lambda utxo: utxo.output.amount.coin)
    return utxo

def aiken_blueprint_apply_hex_params(plutus_json_path: str, hex_params: List[str]) -> dict:
    """
    Apply a list of hex-encoded parameters to a Plutus blueprint using `aiken blueprint apply`.

    :param plutus_json_path: Path to the initial plutus.json file
    :param hex_params: List of parameters to apply (as hex-encoded strings)
    :return: Fully parameterized blueprint as a dictionary

    **Example**::

        >>> desc = cbor2.dumps(b'my cool validator').hex()
        >>> oref = OutputReferenceHack(utxo.input.transaction_id.to_cbor(), utxo.input.index)
        >>> blueprint = aiken_blueprint_apply_hex_params('./plutus.json', [desc, oref])
    """
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as temp_out:
        temp_out_path = temp_out.name
        current_blueprint_path = plutus_json_path
        for hex_param in hex_params:
            cmd = [
                'aiken', 'blueprint', 'apply',
                '--in', current_blueprint_path,
                hex_param,
                '--out', temp_out_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                err_msg = f"Blueprint application failed for parameter {hex_param}: {result.stderr}"
                raise RuntimeError(err_msg)
            current_blueprint_path = temp_out_path
        with open(current_blueprint_path, 'r') as f:
            final_blueprint = json.load(f)
        return final_blueprint

def read_addr(addr_path: str):
    with open(addr_path, "r") as f:
        return Address.from_primitive(f.read())

# TODO are the bytes ever used, or just the hash?
def validator_bytes_and_hash(validator: dict) -> dict:
    script_bytes = PlutusV3Script(
        bytes.fromhex(validator["validators"][0]["compiledCode"])
    )
    script_hash = ScriptHash(bytes.fromhex(validator["validators"][0]["hash"]))
    return {
        "type": "PlutusV3",
        "script_bytes": script_bytes,
        "script_hash": script_hash,
    }

# def read_validator_path(plutus_json_path: str) -> dict:
#     with open(plutus_json_path, "r") as f:
#         validator = json.load(f)
#     return validator_bytes_and_hash(validator)

@dataclass
class PsOpen(PlutusData):
    CONSTR_ID = 0

# @dataclass
# class PsPublish(PlutusData):
#     CONSTR_ID = 1
#     cids: List[bytes]

# @dataclass
# class PsCollect(PlutusData):
#     CONSTR_ID = 2

@dataclass
class PsClose(PlutusData):
    CONSTR_ID = 1

# Examples of creating different variants
# open_action = PubsubAction.ps_open()
# publish_action = PubsubAction.ps_publish([
#   b'cid1',
#   b'cid2'
# ])
# collect_action = PubsubAction.ps_collect()
# close_action = PubsubAction.ps_close()

def utxo_to_ref_hex(utxo):
    ref = OutputReferenceHack(
        utxo.input.transaction_id.to_cbor(),
        utxo.input.index
    )
    return ref.to_cbor().hex()

def open_channel(
    ctx: OgmiosV6ChainContext,
    sk: PaymentSigningKey,
    addr: Address,
    script: PlutusV3Script,
    mint_fn, # TODO type
    oneshot_utxo: UTxO,
):

    action = Redeemer(data=PsOpen())
    print(f'action={action}')

    assets = mint_fn(1)
    print(f'assets={assets}')

    mint_tx = (
        TransactionBuilder(ctx, mint=assets)
        .add_minting_script(script=script, redeemer=action)
        .add_input(oneshot_utxo)
        .add_input_address(addr)
    )

    mint_tx_signed = mint_tx.build_and_sign([sk], change_address=addr)

    ctx.submit_tx(mint_tx_signed)

    print(f'submitted mint tx with id={mint_tx_signed.id}')
    return mint_tx_signed.id

# usage:
#   mint_fn = channel_nft_minter(script, channel_bytes)
#   mint_assets = mint_fn(1)
#   burn_assets = mint_fn(-1)
def channel_nft_minter(script: PlutusV3Script, channel_bytes: bytes):
    def channel_nft_assets(n_to_mint: int):
        # the quicker from_primitive way has some normalize error here
        channel_nft = AssetName(channel_bytes)
        asset = Asset()
        asset[channel_nft] = n_to_mint
        assets = MultiAsset()
        policy_id = script_hash(script)
        assets[policy_id] = asset
        return assets
    return channel_nft_assets

def utxo_contains_channel_nft(
    policy_id: str,
    channel_bytes: bytes,
    utxo: TransactionOutput
) -> bool:
    try:
        return utxo.output.amount.multi_asset[policy_id].get(AssetName(channel_bytes), 0) == 1
    except Exception as e:
        # print('error:', str(e))
        return False

def find_channel_state(
    ctx: OgmiosV6ChainContext,
    addr: Address,
    policy_id: ScriptHash,
    channel_bytes: bytes
):
    return next((
        u for u in ctx.utxos(addr)
        if utxo_contains_channel_nft(policy_id, channel_bytes, u)
    ))

def close_channel(
    ctx: OgmiosV6ChainContext,
    sk: PaymentSigningKey,
    addr: Address,
    script: PlutusV3Script,
    mint_fn, # TODO type
    channel_bytes: bytes
):

    action = Redeemer(data=PsClose())
    print(f'action={action}')

    assets = mint_fn(-1)
    print(f'assets={assets}')

    policy_id = plutus_script_hash(script) # TODO is this right?
    print(f'policy_id={policy_id}')

    state_utxo = find_channel_state(ctx, addr, policy_id, channel_bytes)
    print(f'state_utxo={state_utxo}')

    burn_tx = (
        TransactionBuilder(ctx, mint=assets)
        .add_minting_script(script=script, redeemer=action)
        .add_input(state_utxo)
        .add_input_address(addr)
    )

    burn_tx_signed = burn_tx.build_and_sign([sk], change_address=addr)

    ctx.submit_tx(burn_tx_signed)

    print(f'submitted burn tx with id={burn_tx_signed.id}')
    return burn_tx_signed.id

def main(test_num: int):

    ctx  = OgmiosV6ChainContext("172.13.0.3", 1337)
    sk   = PaymentSigningKey.load("keys/me.sk")
    # vk = PaymentVerificationKey.from_signing_key(sk).hash()

    addr = read_addr('keys/me.addr')
    print(f'addr={addr}')

    # this is used to parameterize the validator,
    # and also to name the channel nft
    # TODO is it not needed as a parameter? maybe only oneshot_ref is ok
    channel_bytes = f'pubsub test {test_num}'.encode()
    print(f'channel_bytes={channel_bytes}')

    channel_hex = cbor2.dumps(channel_bytes).hex()
    print(f'channel_hex={channel_hex}')

    oneshot_utxo = pick_oneshot_utxo(ctx, addr)
    oneshot_hex = utxo_to_ref_hex(oneshot_utxo)
    print(f'oneshot_hex={oneshot_hex}')

    # now we can fully specify the validator,
    script_json = aiken_blueprint_apply_hex_params(
        './plutus.json',
        [channel_hex, oneshot_hex]
    )
    # TODO is saving it also useful?
    script_out_path = f'plutus-test-{str(test_num)}.json'
    with open(script_out_path, 'w') as f:
        json.dump(script_json, f, indent=2)
        print(f'saved final plutus script to {script_out_path}')

    script = PlutusV3Script(validator_bytes_and_hash(script_json)['script_bytes'])

    mint_fn = channel_nft_minter(script, channel_bytes)
 
    open_channel(ctx, sk, addr, script, mint_fn, oneshot_utxo)

    # TODO maybe retry this periodically?
    delay_sec = 60
    print(f'waiting {delay_sec} seconds for mint tx to be confirmed...', end='', flush=True)
    time.sleep(delay_sec)
    print('ok')

    close_channel(ctx, sk, addr, script, mint_fn, channel_bytes)

if __name__ == '__main__':
    main(6)
