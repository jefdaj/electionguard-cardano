#!/usr/bin/env python3

# OLD CODE
# import cbor2
# import json
# import os
# import subprocess
# import sys
# import tempfile
# import time
# 
# from dataclasses import dataclass
# from typing import List
# 
# from pycardano import *
# from pycardano.hash import (
#     VerificationKeyHash,
#     TransactionId,
#     ScriptHash,
# )
# 
# # from pprint import pprint
# 
 
# def read_addr(addr_path: str):
#     with open(addr_path, "r") as f:
#         return Address.from_primitive(f.read())
# 
# def read_validator_path(plutus_json_path: str) -> dict:
#     with open(plutus_json_path, "r") as f:
#         validator = json.load(f)
#     return validator_info(validator)

# def utxo_contains_channel_state_nft(
#     policy_id: str,
#     channel_bytes: bytes,
#     utxo: TransactionOutput
# ) -> bool:
#     try:
#         return utxo.output.amount.multi_asset[policy_id].get(AssetName(channel_bytes), 0) == 1
#     except Exception as e:
#         # print('error:', str(e))
#         return False
# 

# def publish_cids(
#     ctx: OgmiosV6ChainContext,
#     sk: PaymentSigningKey,
#     addr: Address,
#     script: PlutusV3Script,
#     channel_bytes: bytes,
#     cids: List[bytes],
# ):
#     print('\n### publish_cids ###')
# 
#     action = Redeemer(data=PsPublish(cids))
#     print(f'action={action}')
# 
#     policy_id: ScriptHash = plutus_script_hash(script)
#     print(f'policy_id={policy_id}')
# 
#     state_utxo = find_channel_state_utxo(ctx, policy_id, channel_bytes)
#     print(f'state_utxo={state_utxo}')
# 
#     # Check UTxO creation details
#     # print(f"UTxO Address: {state_utxo.output.address}")
#     # print(f"UTxO Address Type: {state_utxo.output.address.address_type}")
#     # print(f"UTxO Script Hash: {state_utxo.output.script_hash}")
# 
#     # Inspect the UTxO more thoroughly
#     print(f"UTxO Full Details: {state_utxo}")
#     print(f"UTxO Assets: {state_utxo.output.amount}")
# 
#     # Check for the state NFT
#     # TODO do we also need to drill down to channel name before saying we found it?
#     # state_nft = state_utxo.output.amount.multi_asset.get(policy_id)
#     # if state_nft:
#     #     print(f"State NFT found: {state_nft}")
# 
#     # TODO is withdrawal script the right idea? see videos and specs if needed
#     # TODO best guess at what's wrong for tonight: you need to send the NFT -> the script address, not keep it when opening
#     publish_tx = (
#         TransactionBuilder(ctx)
#         .add_script_input(state_utxo, script=script, redeemer=action) # TODO aha! address error thing happens here
#         .add_input_address(addr) # TODO is this needed for fees? what about once you add a pool of funds for that?
#     )
# 
#     # TODO why isn't there a simple method for this like mint and withdrawal?
#     # script_witness = TransactionWitnessSet()
#     # script_witness.plutus_scripts = [script]
#     # script_witness.plutus_data = [action]
#     # publish_tx.witness_set = script_witness
# 
#     publish_tx_signed = publish_tx.build_and_sign([sk], change_address=addr)
# 
#     ctx.submit_tx(publish_tx_signed)
# 
#     print(f'submitted publish tx with id={publish_tx_signed.id}')
#     return publish_tx_signed.id
# 
 
# def main(channel_name: str):
# 
#     print('### main ###')
# 
#     ctx  = OgmiosV6ChainContext("localhost", 1337)
#     sk   = PaymentSigningKey.load("keys/me.sk")
#     # vk = PaymentVerificationKey.from_signing_key(sk).hash()
# 
#     addr = read_addr('keys/me.addr')
#     print(f'addr={addr}')
# 
#     # this is used to parameterize the validator,
#     # and also to name the channel nft
#     # TODO is it not needed as a parameter? maybe only oneshot_ref is ok

channel_bytes = channel_name.encode()
channel_hex = cbor2.dumps(channel_bytes).hex()
oneshot_utxo = pick_oneshot_utxo(ctx, addr)
oneshot_hex = utxo_to_ref_hex(oneshot_utxo)
script_json = aiken_blueprint_apply_hex_params(
    './plutus.json',
    [channel_hex, oneshot_hex]
)
# TODO is saving it also useful?
script_out_path = f'plutus-{channel_name}.json'
with open(script_out_path, 'w') as f:
    json.dump(script_json, f, indent=2)
    print(f'saved final plutus script to {script_out_path}')
script = PlutusV3Script(validator_bytes_and_hash(script_json)['script_bytes'])

script = PubsubContract(plutus_json_path='./plutus.json', oneshot_utxo=oneshot_utxo)

#     mint_fn = channel_nft_minter(script, channel_bytes)
#     open_txid = open_channel(ctx, sk, addr, script, mint_fn, oneshot_utxo)
#     wait_for_tx_confirmation(ctx, open_txid)
# 
#     # for now, just publish 3 little CID lists
#     # for n in range(1, 3, 2):
#     #     try:
#     #         cids = [f'cid {n}'.encode(), f'cid {n+1}'.encode()]
#     #         # TODO should addr here be the script addr rather than mine?
#     #         pub_txid = publish_cids(ctx, sk, addr, script, channel_bytes, cids)
#     #         wait_for_tx_confirmation(ctx, pub_txid)
#     #     except Exception as e:
#     #         print(f'ERROR: {e}')
#     #         time.sleep(300) # TODO does this help the burn tx go thru in case of exceptions?
#     input('ready to close the channel?')
# 
#     # TODO addr here must be correct, right?
#     close_txid = close_channel(ctx, sk, addr, script, mint_fn, channel_bytes)
#     wait_for_tx_confirmation(ctx, close_txid)
# 
# if __name__ == '__main__':
#     channel_name = sys.argv[1]
#     main(channel_name)
