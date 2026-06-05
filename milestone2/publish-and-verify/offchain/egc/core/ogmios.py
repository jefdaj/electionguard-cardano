# TODO rename node everywhere?

import asyncio
import json
import websockets

from typing import Any, Dict
from pycardano import *

# TODO is there really not a built in convenience function or constant for this?
# TODO where should it live?
LOVELACE_PER_ADA = 1_000_000

# TODO load these from somewhere?

OGMIOS_HOST = "localhost"
OGMIOS_PORT = 1337
OGMIOS_CTX = OgmiosV6ChainContext(
    host=OGMIOS_HOST,
    port=OGMIOS_PORT,
    network=Network.TESTNET
)

# TODO rename to make it more obvious this is for the --since args?
# TODO and also to check if ogmios is up I guess
async def query_network_tip() -> dict:
    # TODO is there an equivalent context function?
    url = f"ws://{OGMIOS_HOST}:{OGMIOS_PORT}"
    async with websockets.connect(url) as ws:
        request = {
            "jsonrpc": "2.0",
            "method": "queryNetwork/tip",
            "params": {},
            "id": "get-network-tip",
        }
        await ws.send(json.dumps(request))
        raw = await ws.recv()
        response = json.loads(raw)

        if "error" in response:
            raise RuntimeError(f"Ogmios error: {response['error']}")

        # Newer Ogmios: result is directly the point: { "slot": ..., "id": ... }
        result = response.get("result")
        if not isinstance(result, dict) or "slot" not in result or "id" not in result:
            raise RuntimeError(f"Unexpected Ogmios response: {response}")

        # make it more obvious for my kupo --since use case
        slot = result["slot"]
        result["block_hash"] = result["id"]
        del result["id"]
        return result
        # return json.dumps(result, indent=2)

# TODO what's the proper idiom for this?
# TODO should this take OGMIOS_CTX as an argument?
def query_network_tip_sync() -> dict:
    return asyncio.run(query_network_tip())

def top_up_to_min_ada(output: UTxO):
    """The minimum lovelace for a UTXO depends on the serialized size of the
    output, which includes the coin field itself. In most cases this doesn't
    matter, but in edge cases: A small coin value serializes to fewer bytes than a
    large one.  After you bump coin, the output size could cross a threshold that
    changes the minimum. In practice this rarely causes issues because the min
    lovelace calculation has enough headroom, but if you want to be defensive, you
    can loop until it stabilizes.
    """
    for _ in range(3):  # shouldn't need more than 2 iterations
        min_lv = min_lovelace(OGMIOS_CTX, output)
        new_coin = max(output.amount.coin, min_lv)
        if output.amount.coin == new_coin:
            break
        output.amount.coin = new_coin

def set_out_value_and_fee(
    txb: TransactionBuilder,
    in_value: Value,
    out_utxo: TransactionOutput,
) -> None:
    """For a 1-in/1-out continuation pattern (no change output):
    set out_utxo.amount.coin = in_value.coin - fee, iterating until the fee
    stabilizes. Mutates out_utxo and txb.fee in place.
    """
    # Seed with a plausible coin value so CBOR-size estimation is realistic.
    out_utxo.amount.coin = in_value.coin

    fee = 0
    for _ in range(5):
        # _estimate_fee() reads txb.fee internally to build the body, so we
        # need to set it first; it also accounts for redeemer ex-units that
        # have already been evaluated.
        txb.fee = fee if fee else max_tx_fee(OGMIOS_CTX)  # overestimate on first pass
        new_fee = txb._estimate_fee()
        new_coin = in_value.coin - new_fee

        # Defensive min-ADA check
        min_lv = min_lovelace(OGMIOS_CTX, out_utxo)
        if new_coin < min_lv:
            raise ValueError(
                f"Script UTxO under-funded: have {in_value.coin} lovelace, "
                f"need {min_lv + new_fee} (min_ada {min_lv} + fee {new_fee})"
            )

        if out_utxo.amount.coin == new_coin and txb.fee == new_fee:
            txb.fee = new_fee
            return
        out_utxo.amount.coin = new_coin
        fee = new_fee

    txb.fee = fee
