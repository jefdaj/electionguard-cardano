import json

from os import makedirs
from os.path import dirname
from pathlib import Path
from pycardano import PlutusV3Script, ScriptHash, UTxO, Address, Network

from .utils import PLUTUS_JSON_PATH, utxo_to_ref_hex, aiken_blueprint_apply_hex_params

class PubsubScript:

    def __init__(self, oneshot_utxo: UTxO):

        self.oneshot_utxo = oneshot_utxo
        self.oneshot_hex = utxo_to_ref_hex(self.oneshot_utxo)
        self._json_dict = self.apply_params()

        validators = self._json_dict["validators"]
        mint_validator  = next(v for v in validators if 'mint' in v['title'])
        spend_validator = next(v for v in validators if 'spend' in v['title'])

        self.mint_script  = PlutusV3Script(bytes.fromhex(  mint_validator["compiledCode"] ))
        self.spend_script = PlutusV3Script(bytes.fromhex( spend_validator["compiledCode"] ))

        # The policy_id comes from the mint validator hash
        self.policy_id = ScriptHash(bytes.fromhex(mint_validator["hash"]))

        # The address comes from the spend validator hash
        self.address = Address(
            payment_part=ScriptHash(bytes.fromhex(spend_validator["hash"])),
            network=Network.TESTNET
        )

        self.save_json()

    def __repr__(self) -> str:
        # TODO include oneshot_utxo, address, json path
        return f"PubsubScript(oneshot_hex={self.oneshot_hex[:16]}..., policy_id={str(self.policy_id)[:16]}...)"

    def apply_params(self) -> dict:
        print(f"Oneshot UTXO being used:")
        print(f"  tx_hash: {self.oneshot_utxo.input.transaction_id.payload.hex()}")
        print(f"  index: {self.oneshot_utxo.input.index}")
        hex_params = [self.oneshot_hex]
        return aiken_blueprint_apply_hex_params(PLUTUS_JSON_PATH, hex_params)

    def default_json_path(self) -> Path:
        return PLUTUS_JSON_PATH.replace('.json', '-' + self.oneshot_hex + '.json')

    def save_json(self, plutus_json_path: Path = None):
        if plutus_json_path is None:
            plutus_json_path = self.default_json_path()
        makedirs(dirname(plutus_json_path), exist_ok=True)
        with open(plutus_json_path, 'w') as f:
            json.dump(self._json_dict, f, indent=2) # TODO pydantic style?
        print(f'saved {plutus_json_path}')
