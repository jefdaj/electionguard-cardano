# TODO rename node everywhere?

import asyncio
import json
import websockets
import time

from typing import Any, Dict
from pycardano import *

from .wallet import KeyPair

import logging

LOG = logging.getLogger(__name__)

# TODO is there really not a built in convenience function or constant for this?
# TODO where should it live?
LOVELACE_PER_ADA = 1_000_000

COLLATERAL_LOVELACE = 5_000_000

# TODO load these from somewhere?

OGMIOS_HOST = "localhost"
OGMIOS_PORT = 1337
OGMIOS_CTX = OgmiosV6ChainContext(
    host=OGMIOS_HOST,
    port=OGMIOS_PORT,
    network=Network.TESTNET
)

OGMIOS_POLL_SEC    =   3.0
OGMIOS_TIMEOUT_SEC = 300.0

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

def ensure_collateral_utxo(
    # ctx,
    # sk: SigningKey,
    # addr: Address,
    key_pair: KeyPair,
    # amount: int = COLLATERAL_LOVELACE,
    # timeout: float = OGMIOS_TIMEOUT_SEC,
    # poll_interval: float = OGMIOS_POLL_SEC,
) -> UTxO:
    """Return a pure-ADA UTxO at `addr` holding exactly `COLLATERAL_LOVELACE` lovelace,
    creating one by self-payment if none exists.

    Suitable for use as a Plutus script collateral input: the returned UTxO
    is guaranteed to be vkey-locked (at `addr`), pure ADA (no native assets),
    and of exact size (so it isn't accidentally a large general UTxO).

    Args:
        key_pair.sk: The PaymentSigningKey controlling `addr`. Used only if a
                     new UTxO must be created.
        key_pair.addr: The Address to search at and, if needed, send to.

    Returns:
        A UTxO at `addr` with `COLLATERAL_LOVELACE` lovelace and no multi-asset.

    Raises:
        TimeoutError: If a newly submitted self-payment doesn't appear
            within `OGMIOS_TIMEOUT_SEC` seconds.
    """
    existing = _find_exact_ada_utxo(key_pair.addr, COLLATERAL_LOVELACE)
    if existing is not None:
        LOG.debug(
            'Found existing collateral UTxO: %s#%d (%d lovelace)',
            existing.input.transaction_id, existing.input.index,
            existing.output.amount.coin,
        )
        return existing

    LOG.info(
        'No %d-lovelace pure-ADA UTxO at %s; creating one',
        COLLATERAL_LOVELACE, key_pair.addr,
    )

    txb = TransactionBuilder(OGMIOS_CTX)
    txb.add_input_address(key_pair.addr)
    txb.add_output(TransactionOutput(address=key_pair.addr, amount=Value(coin=COLLATERAL_LOVELACE)))
    tx = txb.build_and_sign(signing_keys=[key_pair.sk], change_address=key_pair.addr)
    OGMIOS_CTX.submit_tx(tx)
    LOG.info('Submitted collateral-creation tx id=%s', tx.id)

	# TODO refactor to deduplicate this with the version in Publisher
    deadline = time.time() + OGMIOS_TIMEOUT_SEC
    while time.time() < deadline:
        for u in OGMIOS_CTX.utxos(key_pair.addr):
            if (
                u.input.transaction_id == tx.id
                and _is_exact_ada(u, COLLATERAL_LOVELACE)
            ):
                LOG.debug(
                    'New collateral UTxO confirmed: %s#%d',
                    u.input.transaction_id, u.input.index,
                )
                return u
        time.sleep(OGMIOS_POLL_SEC)

	# TODO custom egc error classes?
    raise TimeoutError(
        f'Collateral UTxO from tx {tx.id} did not appear at {key_pair.addr} '
        f'within {OGMIOS_TIMEOUT_SEC}s'
    )


def _find_exact_ada_utxo(addr: Address, amount: int):
    """Return a UTxO at `addr` holding exactly `amount` lovelace and no
    other assets, or None."""
    for u in OGMIOS_CTX.utxos(addr):
        if _is_exact_ada(u, amount):
            return u
    return None


def _is_exact_ada(u: UTxO, amount: int) -> bool:
    """True iff `u` holds exactly `amount` lovelace and no native assets."""
    val = u.output.amount
    if isinstance(val, Value):
        return val.coin == amount and not val.multi_asset
    # Some chain contexts return a bare int for ADA-only outputs
    return val == amount
