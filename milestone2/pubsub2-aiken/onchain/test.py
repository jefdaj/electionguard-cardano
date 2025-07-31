#!/usr/bin/env python3

from pycardano import *
from pycardano.hash import (
    VerificationKeyHash,
    TransactionId,
    ScriptHash,
)
import cbor2
import json
import os
from dataclasses import dataclass
# from tempfile import TemporaryDirectory
import tempfile
# from shutil import copytree
# import shutil
from pprint import pprint
import subprocess
from typing import List


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

# TODO double check this matches the definitions in lib/types.ak
# TODO separate definition of CID?
@dataclass
class PubsubAction(PlutusData):
    CONSTR_TAG_PSOPEN    = 0
    CONSTR_TAG_PSPUBLISH = 1
    CONSTR_TAG_PSCOLLECT = 2
    CONSTR_TAG_PSCLOSE   = 3

    constructor: int
    cids: List[bytes] = None

    @classmethod
    def ps_open(cls):
        return cls(constructor=cls.CONSTR_TAG_PSOPEN)

    @classmethod
    def ps_publish(cls, cids: List[bytes]):
        return cls(constructor=cls.CONSTR_TAG_PSPUBLISH, cids=cids)

    @classmethod
    def ps_collect(cls):
        return cls(constructor=cls.CONSTR_TAG_PSCOLLECT)

    @classmethod
    def ps_close(cls):
        return cls(constructor=cls.CONSTR_TAG_PSCLOSE)

# Examples of creating different variants
# open_action = PubsubAction.ps_open()
# publish_action = PubsubAction.ps_publish([
#   b'cid1', 
#   b'cid2'
# ])
# collect_action = PubsubAction.ps_collect()
# close_action = PubsubAction.ps_close()

def main():

    ctx  = OgmiosV6ChainContext("172.13.0.3", 1337)
    sk   = PaymentSigningKey.load("keys/me.sk")
    vk   = PaymentVerificationKey.from_signing_key(sk).hash()
    addr = read_addr('keys/me.addr') # TODO is this also vk?
    # print('ctx:', ctx)
    # print('sk:', sk)
    # print('vk:', vk)
    # print('addr:', addr)

    # note this is also the name of the NFT asset minted to track channel state
    channel_bytes = b'test channel 001'
    channel_hex = cbor2.dumps(channel_bytes).hex()
    # print('channel_hex:', channel_hex)

    oneshot_utxo = pick_oneshot_utxo(ctx, addr)
    oneshot_ref = OutputReferenceHack(
        oneshot_utxo.input.transaction_id.to_cbor(),
        oneshot_utxo.input.index
    )
    oneshot_hex = oneshot_ref.to_cbor().hex()
    # print('oneshot_hex:', oneshot_hex)

    script_json = aiken_blueprint_apply_hex_params(
        './plutus.json',
        [channel_hex, oneshot_hex]
    )
    # print('script_json:', script_json)

    # TODO is this intermediate dict format helpful?
    script_compiled = validator_bytes_and_hash(script_json)
    script = PlutusV3Script(script_compiled['script_bytes'])

    psopen = Redeemer(data=PubsubAction.ps_open())
    nft = MultiAsset({ script_hash(script): { AssetName.from_primitive(channel_bytes): 1 } })
    mint_tx = (
        TransactionBuilder(ctx, mint=nft)
        .add_minting_script(script=script, redeemer=psopen)
        .add_input_address(addr)
    )
    pprint(mint_tx)

    # mint_tx_signed = mint_tx.build_and_sign([sk], change_address=addr)
    # pprint(mint_tx_signed)

if __name__ == '__main__':
    main()
