#!/usr/bin/env python3

from pycardano import *
from pycardano.hash import (
    VerificationKeyHash,
    TransactionId,
    ScriptHash,
)
import json
import os
import sys
from dataclasses import dataclass

@dataclass
class HelloWorldRedeemer(PlutusData):
    CONSTR_ID = 0
    msg: bytes

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

def unlock(
    addr_path: str,
    utxo: UTxO,
    from_script: PlutusV3Script,
    redeemer: Redeemer,
    signing_key: PaymentSigningKey,
    owner: VerificationKeyHash,
    context: OgmiosV6ChainContext,
) -> TransactionId:
    # read addresses
    with open(addr_path, "r") as f:
        input_address = Address.from_primitive(f.read())
 
    # build transaction
    builder = TransactionBuilder(context=context)
    builder.add_script_input(
        utxo=utxo,
        script=from_script,
        redeemer=redeemer,
    )
    builder.add_input_address(input_address)
    builder.add_output(
        TransactionOutput(
            address=input_address,
            amount=utxo.output.amount.coin,
        )
    )
    builder.required_signers = [owner]
    signed_tx = builder.build_and_sign(
        signing_keys=[signing_key],
        change_address=input_address,
    )
 
    # submit transaction
    context.submit_tx(signed_tx)

    return signed_tx.id

def get_utxo_from_str(context, tx_id: str, contract_address: Address) -> UTxO:
    for utxo in context.utxos(str(contract_address)):
        if str(utxo.input.transaction_id) == tx_id:
            return utxo
    raise Exception(f"UTxO not found for transaction {tx_id}")

def main(tx_id: str):
    # TODO thread host and port from top level arion-compose
    context = OgmiosV6ChainContext("172.13.0.3", 1337)
    signing_key = PaymentSigningKey.load("keys/me.sk")
    validator = read_validator()
    utxo = get_utxo_from_str(context, tx_id, Address(
        payment_part = validator["script_hash"],
        network=Network.TESTNET,
    ))
    redeemer = Redeemer(data=HelloWorldRedeemer(msg=b"Hello, World!"))
    tx_hash = unlock(
        addr_path="keys/me.addr",
        utxo=utxo,
        from_script=validator["script_bytes"],
        redeemer=redeemer,
        signing_key=signing_key,
        owner=PaymentVerificationKey.from_signing_key(signing_key).hash(),
        context=context,
    )
    print(
        f"2 tADA unlocked from the contract\n\tTx ID: {tx_hash}\n\tRedeemer: {redeemer.to_cbor_hex()}"
    )

if __name__ == '__main__':
    tx_id = sys.argv[1]
    main(tx_id)
