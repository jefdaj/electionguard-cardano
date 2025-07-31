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

def pick_oneshot_ref(context, addr):
    utxos = context.utxos(addr)
    if not utxos:
        raise Exception(f'addr {addr} has no UTXOs')
    largest_utxo = max(utxos, key=lambda utxo: utxo.output.amount.coin)
    # print(largest_utxo)
    # print(largest_utxo.to_cbor().hex())
    oref = f'{largest_utxo.input.transaction_id}#{largest_utxo.input.index}'
    return oref

# def parameterize_aiken_script(
#     project_path: str,
#     validator_name: str,
#     params: list[tuple[str, str]]  # [(param_name, param_value), ...]
# ):
#     with TemporaryDirectory() as tmpdir:
#         copytree(project_path, tmpdir, dirs_exist_ok=True)
# 
#         apply_params = [f"-p {k}={v}" for k, v in params]
#         cmd = [
#             "aiken", "blueprint", "apply",
#             *apply_params
#         ]
#         print(cmd)
# 
#         apply_result = subprocess.run(
#             cmd,
#             cwd=tmpdir,
#             capture_output=True,
#             text=True
#         )
# 
#         if apply_result.returncode != 0:
#             raise RuntimeError(f"Aiken apply failed: {apply_result.stderr}")
# 
#         build_result = subprocess.run(
#             ["aiken", "build"],
#             cwd=tmpdir,
#             capture_output=True,
#             text=True
#         )
# 
#         if build_result.returncode != 0:
#             raise RuntimeError(f"Aiken build failed: {build_result.stderr}")
# 
#         # Load the Plutus JSON
#         # plutus_json_path = os.path.join(tmpdir, 'build', 'plutus.json')
#         # with open(plutus_json_path, 'r') as f:
#         #     plutus_json = json.load(f)
#         # Find the specific validator
#         # validator = next(
#         #     (v for v in plutus_json['validators']
#         #      if v['title'] == validator_name),
#         #     None
#         # )
#         # if not validator:
#         #     raise ValueError(f"Validator {validator_name} not found")
#         # return validator['compiledCode']

# def parameterize_aiken_script(plutus_json_path: str, params: list[str]):

def parameterize_blueprint(plutus_json_path, parameters):
    """
    Parameterize a Plutus blueprint with a list of parameters, applied sequentially.
    
    :param plutus_json_path: Path to the original plutus.json file
    :param parameters: List of parameters to apply (as hex-encoded strings)
    :return: Fully parameterized blueprint as a dictionary
    """

    # Create a temporary file for intermediate outputs
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as temp_out:
        temp_out_path = temp_out.name
    
    try:
        # Start with the original blueprint
        current_blueprint_path = plutus_json_path
        
        # Apply parameters sequentially
        for param in parameters:
            # Construct the command
            cmd = ['aiken', 'blueprint', 'apply', 
                   '--in', current_blueprint_path, 
                   param,
                   '--out', temp_out_path]
            
            print('cmd:', cmd)
            
            # Run the command
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Check for errors
            if result.returncode != 0:
                raise RuntimeError(f"Blueprint application failed for parameter {param}: {result.stderr}")
            
            # Update the current blueprint path for the next iteration
            current_blueprint_path = temp_out_path
        
        # Read the final parameterized JSON
        with open(current_blueprint_path, 'r') as f:
            parameterized_blueprint = json.load(f)
        
        return parameterized_blueprint
    
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_out_path):
            os.unlink(temp_out_path)

def read_addr(addr_path: str):
    with open(addr_path, "r") as f:
        return Address.from_primitive(f.read())

def read_validator() -> dict:
    with open("plutus.json", "r") as f:
        validator = json.load(f)
    script_bytes = PlutusV3Script(
        bytes.fromhex(validator["validators"][0]["compiledCode"])
    )
    script_hash = ScriptHash(bytes.fromhex(validator["validators"][0]["hash"]))
    return {
        "type": "PlutusV3",
        "script_bytes": script_bytes,
        "script_hash": script_hash,
    }

def main():

    # TODO thread host and port from top level arion-compose
    context = OgmiosV6ChainContext("172.13.0.3", 1337)
    signing_key = PaymentSigningKey.load("keys/me.sk")
    owner = PaymentVerificationKey.from_signing_key(signing_key).hash()
    addr = read_addr('keys/me.addr')
    print(addr)
    # oneshot_ref = pick_oneshot_ref(context, addr)
    channel_name = cbor2.dumps(b'test1_channel').hex() # note the b!
    print('channel_name:', channel_name)
    oneshot_ref = pick_oneshot_ref(context, addr)
    print('oneshot_ref:', oneshot_ref)
    # validator = read_validator()
    # print(
    #     f"2 tADA locked into the contract\n\tTx ID: {tx_hash}\n\tDatum: {datum.to_cbor_hex()}"
    # )

    # TODO try parameterizing with one of the js libraries and see what cbor it generates!
    #      then mimic the same thing in python

    # fails because i haven't figured out how to encode the oneshot_ref properly:
    # script_cbor = parameterize_blueprint('plutus.json', [channel_name, oneshot_ref])

    script_cbor = parameterize_blueprint('./plutus.json', [channel_name])
    # pprint(script_cbor)

if __name__ == '__main__':
    main()
