import json
import subprocess

from dataclasses import dataclass
from pycardano import PlutusData
from typing import List
from tempfile import NamedTemporaryFile

# This is a temporary hack for use with `aiken blueprint apply`
# See https://github.com/Python-Cardano/pycardano/issues/439
# TODO revisit once native apply_params support is released
@dataclass
class OutputReferenceHack(PlutusData):
    CONSTR_ID = 0
    transaction_id: bytes
    index: int

# TODO move to different util module?
def pick_oneshot_utxo(context, addr):
    # No particular logic to max here; any UTXO should work for the initial tests
    utxos = context.utxos(addr)
    if not utxos:
        raise Exception(f'addr {addr} has no UTXOs')
    utxo = max(utxos, key=lambda utxo: utxo.output.amount.coin)
    return utxo

def utxo_to_ref_hex(utxo):
    ref = OutputReferenceHack(
        utxo.input.transaction_id.to_cbor(),
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
        >>> oref = OutputReferenceHack(utxo.input.transaction_id.to_cbor(), utxo.input.index)
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
