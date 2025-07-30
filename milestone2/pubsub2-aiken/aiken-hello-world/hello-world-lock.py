#!/usr/bin/env python3

# references:
# https://aiken-lang.org/example--hello-world/end-to-end/pycardano
# https://ogmios-python.readthedocs.io/en/latest/examples/build_tx_pycardano.html

from pycardano import *
import os

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

if __name__ == '__main__':
	main()
