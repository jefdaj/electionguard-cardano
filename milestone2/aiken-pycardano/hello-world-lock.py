#!/usr/bin/env python3

# references:
# https://aiken-lang.org/example--hello-world/end-to-end/pycardano
# https://ogmios-python.readthedocs.io/en/latest/examples/build_tx_pycardano.html

from pycardano import *
from pycardano.hash import (
    VerificationKeyHash,
    TransactionId,
    ScriptHash,
)
import json
import os
from dataclasses import dataclass

@dataclass
class HelloWorldDatum(PlutusData):
    CONSTR_ID = 0
    owner: bytes

def read_validator() -> dict:

    with open("plutus.json", "r") as f:
        validator = json.load(f)

    script_bytes = PlutusV3Script(
        bytes.fromhex(
            validator["validators"][0]["compiledCode"]
        )
    )

    script_hash = ScriptHash(
        bytes.fromhex(
            validator["validators"][0]["hash"]
        )
    )

    return {
        "type": "PlutusV3",
        "script_bytes": script_bytes,
        "script_hash": script_hash,
    }

def lock(
    addr_path: str,
    amount: int,
    into: ScriptHash,
    datum: PlutusData,
    signing_key: PaymentSigningKey,
    context: OgmiosV6ChainContext,
) -> TransactionId:

    # read addresses
    with open(addr_path, "r") as f:
        input_address = Address.from_primitive(f.read())
    contract_address = Address(
        payment_part = into,
        network=Network.TESTNET,
    )
 
    # build transaction
    builder = TransactionBuilder(context=context)
    builder.add_input_address(input_address)
    builder.add_output(
        TransactionOutput(
            address=contract_address,
            amount=amount,
            datum=datum,
        )
    )
    signed_tx = builder.build_and_sign(
        signing_keys=[signing_key],
        change_address=input_address,
    )
 
    # submit transaction
    context.submit_tx(signed_tx)

    return signed_tx.id

def main():
    # TODO thread host and port from top level arion-compose
    context = OgmiosV6ChainContext("localhost", 1337)
    signing_key = PaymentSigningKey.load("keys/me.sk")
    owner = PaymentVerificationKey.from_signing_key(signing_key).hash()
    datum = HelloWorldDatum(owner=owner.to_primitive())
    validator = read_validator()
    tx_hash = lock(
        addr_path="keys/me.addr",
        amount=2_000_000,
        into=validator["script_hash"],
        datum=datum,
        signing_key=signing_key,
        context=context,
    )
    print(
        f"2 tADA locked into the contract\n\tTx ID: {tx_hash}\n\tDatum: {datum.to_cbor_hex()}"
    )

if __name__ == '__main__':
    main()
