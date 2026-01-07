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
# # This is a temporary hack for use with `aiken blueprint apply`
# # See https://github.com/Python-Cardano/pycardano/issues/439
# # TODO revisit once native apply_params support is released
# @dataclass
# class OutputReferenceHack(PlutusData):
#     CONSTR_ID = 0
#     transaction_id: bytes
#     index: int
# 
# def pick_oneshot_utxo(context, addr):
#     # No particular logic to max here; any UTXO should work for the initial tests
#     utxos = context.utxos(addr)
#     if not utxos:
#         raise Exception(f'addr {addr} has no UTXOs')
#     utxo = max(utxos, key=lambda utxo: utxo.output.amount.coin)
#     return utxo
# 
# def aiken_blueprint_apply_hex_params(plutus_json_path: str, hex_params: List[str]) -> dict:
#     """
#     Apply a list of hex-encoded parameters to a Plutus blueprint using `aiken blueprint apply`.
# 
#     :param plutus_json_path: Path to the initial plutus.json file
#     :param hex_params: List of parameters to apply (as hex-encoded strings)
#     :return: Fully parameterized blueprint as a dictionary
# 
#     **Example**::
# 
#         >>> desc = cbor2.dumps(b'my cool validator').hex()
#         >>> oref = OutputReferenceHack(utxo.input.transaction_id.to_cbor(), utxo.input.index)
#         >>> blueprint = aiken_blueprint_apply_hex_params('./plutus.json', [desc, oref])
#     """
#     with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as temp_out:
#         temp_out_path = temp_out.name
#         current_blueprint_path = plutus_json_path
#         for hex_param in hex_params:
#             cmd = [
#                 'aiken', 'blueprint', 'apply',
#                 '--in', current_blueprint_path,
#                 hex_param,
#                 '--out', temp_out_path
#             ]
#             result = subprocess.run(cmd, capture_output=True, text=True)
#             if result.returncode != 0:
#                 err_msg = f"Blueprint application failed for parameter {hex_param}: {result.stderr}"
#                 raise RuntimeError(err_msg)
#             current_blueprint_path = temp_out_path
#         with open(current_blueprint_path, 'r') as f:
#             final_blueprint = json.load(f)
#         return final_blueprint
# 
# def read_addr(addr_path: str):
#     with open(addr_path, "r") as f:
#         return Address.from_primitive(f.read())
# 
# # TODO are the bytes ever used, or just the hash?
# def validator_bytes_and_hash(validator: dict) -> dict:
#     script_bytes = PlutusV3Script(
#         bytes.fromhex(validator["validators"][0]["compiledCode"])
#     )
#     script_hash = ScriptHash(bytes.fromhex(validator["validators"][0]["hash"]))
#     return {
#         "type": "PlutusV3",
#         "script_bytes": script_bytes,
#         "script_hash": script_hash,
#     }
# 
# # def read_validator_path(plutus_json_path: str) -> dict:
# #     with open(plutus_json_path, "r") as f:
# #         validator = json.load(f)
# #     return validator_bytes_and_hash(validator)
# 
# @dataclass
# class PsOpen(PlutusData):
#     CONSTR_ID = 0
# 
# @dataclass
# class PsPublish(PlutusData):
#     CONSTR_ID = 1
#     cids: List[bytes]
# 
# # @dataclass
# # class PsCollect(PlutusData):
# #     CONSTR_ID = 2
# 
# @dataclass
# class PsClose(PlutusData):
#     CONSTR_ID = 2
# 
# # Examples of creating different variants
# # open_action = PubsubAction.ps_open()
# # publish_action = PubsubAction.ps_publish([
# #   b'cid1',
# #   b'cid2'
# # ])
# # collect_action = PubsubAction.ps_collect()
# # close_action = PubsubAction.ps_close()
# 
# def utxo_to_ref_hex(utxo):
#     ref = OutputReferenceHack(
#         utxo.input.transaction_id.to_cbor(),
#         utxo.input.index
#     )
#     return ref.to_cbor().hex()
# 
# # TODO wait could the problem be that the NFT is being given to my wallet rather than the script?
# def open_channel(
#     ctx: OgmiosV6ChainContext,
#     sk: PaymentSigningKey,
#     addr: Address,
#     script: PlutusV3Script,
#     mint_fn, # TODO type
#     oneshot_utxo: UTxO,
# ):
#     print('\n### open_channel ###')
# 
#     action = Redeemer(data=PsOpen())
#     print(f'action={action}')
# 
#     assets = mint_fn(1)
#     print(f'assets={assets}')
# 
#     # Lock the NFT at the script address
#     script_addr = Address(payment_part=plutus_script_hash(script), network=Network.TESTNET)
#     lock_output = TransactionOutput(
#         address=script_addr,
#         amount=Value(
#             2_000_000,   # min ADA with your NFT; adjust as needed
#             assets       # the minted NFT
#         ),
#         # optionally include datum / inline datum here
#         # datum=..., or datum_hash=...
#     )
# 
#     # TODO is the problem that you're sending the NFT to the wrong place here?
#     mint_tx = (
#         TransactionBuilder(ctx, mint=assets)
#         .add_output(lock_output)
#         .add_minting_script(script=script, redeemer=action)
#         .add_input(oneshot_utxo)
#         .add_input_address(addr)
#     )
# 
#     mint_tx_signed = mint_tx.build_and_sign([sk], change_address=addr)
# 
#     ctx.submit_tx(mint_tx_signed)
# 
#     print(f'submitted mint tx with id={mint_tx_signed.id}')
#     return mint_tx_signed.id
# 
# # usage:
# #   mint_fn = channel_nft_minter(script, channel_bytes)
# #   mint_assets = mint_fn(1)
# #   burn_assets = mint_fn(-1)
# def channel_nft_minter(script: PlutusV3Script, channel_bytes: bytes):
#     def channel_nft_assets(n_to_mint: int):
#         # the quicker from_primitive way has some normalize error here
#         channel_nft = AssetName(channel_bytes)
#         asset = Asset()
#         asset[channel_nft] = n_to_mint
#         assets = MultiAsset()
#         policy_id = script_hash(script)
#         assets[policy_id] = asset
#         return assets
#     return channel_nft_assets
# 
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
# # TODO start factoring out some utils/lib?
# def find_channel_state_utxo(
#     ctx: OgmiosV6ChainContext,
#     policy_id: ScriptHash,
#     channel_bytes: bytes
# ):
#     script_addr = Address(payment_part=policy_id, network=Network.TESTNET)
#     matches = list(
#         u for u in ctx.utxos(script_addr)
#         if utxo_contains_channel_state_nft(policy_id, channel_bytes, u)
#     )
#     if len(matches) == 0:
#         print('no such state utxo')
#         return None
#     elif len(matches) > 1:
#         raise Exception(f'found multiple state utxos: {matches}')
#     else:
#         return matches[0]
# 
# # TODO get this working for the case where the utxo is confirmed + consumed between polls
# def wait_for_tx_confirmation(ctx, tx_id: TransactionId, max_seconds: int = 300, interval_seconds: int = 5):
#     tx_id = str(tx_id) # TODO is this the right way?
#     print(f'tx {tx_id} waiting up to {max_seconds} seconds for confirmation', end='', flush=True)
#     waited_seconds = 0
#     while True:
#         time.sleep(interval_seconds)
#         waited_seconds += interval_seconds
#         print('.', end='', flush=True)
#         utxo = ctx.utxo_by_tx_id(tx_id, 0)
#         if utxo is None:
#             if waited_seconds >= max_seconds:
#                 print(' FAIL', flush=True)
#                 raise Exception(f'tx {tx_id} still not confirmed after {waited_seconds} seconds')
#             continue
#         else:
#             print(f' confirmed after {waited_seconds} seconds', flush=True)
#             return
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
# def close_channel(
#     ctx: OgmiosV6ChainContext,
#     sk: PaymentSigningKey,
#     addr: Address,
#     script: PlutusV3Script,
#     mint_fn, # TODO type
#     channel_bytes: bytes
# ):
#     print('\n### close_channel ###')
# 
#     action = Redeemer(data=PsClose())
#     print(f'action={action}')
# 
#     assets = mint_fn(-1)
#     print(f'assets={assets}')
# 
#     policy_id = plutus_script_hash(script)
#     print(f'policy_id={policy_id}')
# 
#     state_utxo = find_channel_state_utxo(ctx, policy_id, channel_bytes)
#     print(f'state_utxo={state_utxo}')
# 
#     burn_tx = (
#         TransactionBuilder(ctx, mint=assets)
#         .add_minting_script(script=script, redeemer=action)
#         .add_input(state_utxo)
#         .add_input_address(addr)
#     )
# 
#     burn_tx_signed = burn_tx.build_and_sign([sk], change_address=addr)
# 
#     ctx.submit_tx(burn_tx_signed)
# 
#     print(f'submitted burn tx with id={burn_tx_signed.id}')
#     return burn_tx_signed.id
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
#     channel_bytes = channel_name.encode()
#     print(f'channel_bytes={channel_bytes}')
# 
#     channel_hex = cbor2.dumps(channel_bytes).hex()
#     print(f'channel_hex={channel_hex}')
# 
#     oneshot_utxo = pick_oneshot_utxo(ctx, addr)
#     oneshot_hex = utxo_to_ref_hex(oneshot_utxo)
#     print(f'oneshot_hex={oneshot_hex}')
# 
#     # now we can fully specify the validator,
#     # TODO should oneshot come before channel name?
#     script_json = aiken_blueprint_apply_hex_params(
#         './plutus.json',
#         [channel_hex, oneshot_hex]
#     )
#     # TODO is saving it also useful?
#     script_out_path = f'plutus-{channel_name}.json'
#     with open(script_out_path, 'w') as f:
#         json.dump(script_json, f, indent=2)
#         print(f'saved final plutus script to {script_out_path}')
# 
#     script = PlutusV3Script(validator_bytes_and_hash(script_json)['script_bytes'])
#     print(f'script: {script}')
# 
#     mint_fn = channel_nft_minter(script, channel_bytes)
# 
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
