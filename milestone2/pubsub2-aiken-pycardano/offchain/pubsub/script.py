import json

from os import makedirs
from pathlib import Path
from pycardano import PlutusV3Script, ScriptHash, UTxO, Address, Network

from .utils import utxo_to_ref_hex, aiken_blueprint_apply_hex_params

# TODO hold up this doesn't go in types

class PubsubScript:

    def __init__(self, raw_plutus_json_path: str, oneshot_utxo: UTxO):
        self._raw_plutus_json_path = Path(raw_plutus_json_path)
        self.oneshot_utxo = oneshot_utxo
        self.oneshot_hex = utxo_to_ref_hex(self.oneshot_utxo)
        self._json_dict = self.apply_params()
        self.bytes = PlutusV3Script( bytes.fromhex(self._json_dict["validators"][0]["compiledCode"] ))
        self.hash  = ScriptHash(     bytes.fromhex(self._json_dict["validators"][0]["hash"        ] ))
        self.address = Address(payment_part=self.hash, network=Network.TESTNET)
        # self.policy_id = plutus_script_hash(self.bytes) # TODO redundant with hash?

    @property
    def policy_id(self):
        return self.hash

    def __repr__(self) -> str:
        # TODO include oneshot_utxo, address, json path
        return f"PubsubScript(oneshot_hex={self.oneshot_hex[:16]}..., policy_id={self.policy_id[:16]}...)"

    def apply_params(self) -> dict:
        hex_params = [self.oneshot_hex]
        return aiken_blueprint_apply_hex_params(self._raw_plutus_json_path, hex_params)

    def default_json_path(self) -> Path:
        p = self._raw_plutus_json_path
        json_path = p.parent / ('pubsub2-' + self.oneshot_hex + '-plutus.json')
        return json_path

    def save_json(self, plutus_json_path: Path = None):
        if plutus_json_path is None:
            plutus_json_path = self.default_json_path()
        makedirs(plutus_json_path.parent, exist_ok=True)
        with open(plutus_json_path, 'w') as f:
            json.dump(self._json_dict, f, indent=2) # TODO pydantic style?
        print(f'saved {plutus_json_path}')
