import json
import subprocess
import logging

from dataclasses import dataclass
from os import makedirs
from os.path import dirname, realpath, splitext
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List, Optional

from ..config import PLUTUS_JSON_PATH

LOG = logging.getLogger(__name__)

from pycardano import * # PlutusData, PlutusV3Script, ScriptHash, UTxO, Address, Network


def pick_oneshot_utxo(context, addr):
    # No particular logic to max here; any UTXO should work for the initial tests
    # TODO pick a smaller one so you can't lock most of the tADA accidentally?
    utxos = context.utxos(addr)
    LOG.debug(f'pick_oneshot_utxo addr:{addr} utxos:{utxos}')
    if not utxos:
        raise Exception(f'addr {addr} has no UTXOs')
    utxo = max(utxos, key=lambda utxo: utxo.output.amount.coin)
    return utxo

# This is a temporary hack for use with `aiken blueprint apply`
# See https://github.com/Python-Cardano/pycardano/issues/439
# TODO revisit once native apply_params support is released
@dataclass
class OutputReferenceHack(PlutusData):
    CONSTR_ID = 0
    transaction_id: bytes
    index: int

def utxo_to_ref_hex(utxo):
    ref = OutputReferenceHack(
        utxo.input.transaction_id.payload,
        utxo.input.index
    )
    return ref.to_cbor().hex()

def aiken_blueprint_apply_hex_params(plutus_json_path: str, hex_params: List[str]) -> dict:
    """
    Apply a list of hex-encoded parameters to a Plutus blueprint using `aiken blueprint apply`.

    :param plutus_json_path: Path to the initial plutus.json file
    :param hex_params: List of parameters to apply (as hex-encoded strings)
    :return: Fully parameterized blueprint as a dictionary

    **Example**::

        >>> desc = cbor2.dumps(b'my cool validator').hex()
        >>> oref = OutputReferenceHack(utxo.input.transaction_id.payload, utxo.input.index)
        >>> blueprint = aiken_blueprint_apply_hex_params('./plutus.json', [desc, oref])
    """
    with NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as temp_out:
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

# TODO remove after splitting out all the code
# class ElectionScript:
#     """
#     A Python object representing the compiled Plutus script.
#     On creation, applies the one-shot UTXO parameter and saves the
#     parameterized JSON in case it's needed later.
# 
#     Examples:
#         >>> # TODO get oneshot utxo
#         >>> script = # TODO fill in
#         >>> script # TODO fill in
#         >>> script.default_json_path() # TODO fill in
#         >>> script.policy_id # TODO fill in
#         >>> script.address # TODO fill in
#     """
#     # TODO variable saying whether it's using the traced or production version
# 
#     def __init__(self, oneshot_utxo: Optional[UTxO] = None, json_path: Optional[str] = None):
# 
#         # TODO when loading from json_path, do we also need to save + load the oneshot_utxo for anything?
#         # TODO for now, oneshot_utxo hash higher priority than json_path... is that a reasonable interface?
#         # TODO don't require the json to be named including the hex
# 
#         if oneshot_utxo is not None:
#             # TODO use oneshot_hex for logging instead?
#             msg =  f"Oneshot UTXO being used:"
#             msg += f"\n  tx_hash: {self.oneshot_utxo.input.transaction_id.payload.hex()}"
#             msg += f"\n  index: {self.oneshot_utxo.input.index}"
#             LOG.debug(msg)
#             self.oneshot_hex = utxo_to_ref_hex(self.oneshot_utxo)
#             LOG.debug(f'oneshot_hex from oneshot_utxo: {self.oneshot_hex}')
#             hex_params = [self.oneshot_hex]
#             json_dict = aiken_blueprint_apply_hex_params(PLUTUS_JSON_PATH, hex_params)
#             self._init_from_json(json_dict)
#             self.save_json()
# 
#         elif json_path is not None:
#             self.oneshot_hex = splitext(json_path.split('-')[-1])[0]
#             LOG.debug(f'oneshot_hex from json_path: {self.oneshot_hex}')
#             with open(json_path, 'r') as f:
#                 json_dict = json.load(f)
#             self._init_from_json(json_dict)
# 
#         else:
#             raise Exception('must init with either a oneshot_utxo or existing json_path')
# 
#     def _init_from_json(self, json_dict):
# 
#         self._json_dict = json_dict
#         validators = self._json_dict["validators"]
#         mint_validator  = next(v for v in validators if 'mint'  in v['title'])
#         spend_validator = next(v for v in validators if 'spend' in v['title'])
# 
#         self.mint_script  = PlutusV3Script(bytes.fromhex(  mint_validator["compiledCode"] ))
#         self.spend_script = PlutusV3Script(bytes.fromhex( spend_validator["compiledCode"] ))
# 
#         # The policy_id comes from the mint validator hash
#         self.policy_id = ScriptHash(bytes.fromhex(mint_validator["hash"]))
# 
#         # The address comes from the spend validator hash
#         self.address = Address(
#             payment_part=ScriptHash(bytes.fromhex(spend_validator["hash"])),
#             network=Network.TESTNET
#         )
# 
# 
#     def __repr__(self) -> str:
#         # TODO include oneshot_utxo, address, json path
#         return f"ElectionScript(policy_id={str(self.policy_id)[:16]}...)"
# 
#     def apply_params(self, hex_params) -> dict:
#         return aiken_blueprint_apply_hex_params(PLUTUS_JSON_PATH, hex_params)
# 
#     def default_json_path(self) -> Path:
#         return PLUTUS_JSON_PATH.replace('.json', '-' + self.oneshot_hex + '.json')
# 
#     def save_json(self, plutus_json_path: Path = None):
#         if plutus_json_path is None:
#             plutus_json_path = self.default_json_path()
#         makedirs(dirname(plutus_json_path), exist_ok=True)
#         with open(plutus_json_path, 'w') as f:
#             json.dump(self._json_dict, f, indent=2) # TODO pydantic style?
#         LOG.debug(f'saved {plutus_json_path}')
