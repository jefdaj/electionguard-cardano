import aiohttp
import asyncio
import json
import websockets
import time
import math
# import re
import ast

from typing import Any, Dict, Optional, Callable
from pycardano import *
from ogmios.errors import ResponseError
from pycardano.utils import max_tx_fee, min_lovelace_post_alonzo


from .wallet import Wallet

import logging


LOG = logging.getLogger(__name__)

# TODO is there really not a built in convenience function or constant for this?
# TODO where should it live?
LOVELACE_PER_ADA = 1_000_000

COLLATERAL_ADA = 5
COLLATERAL_LOVELACE = COLLATERAL_ADA * LOVELACE_PER_ADA

OGMIOS_HOST = "localhost"
OGMIOS_PORT = 1337
OGMIOS_CTX = OgmiosV6ChainContext(
    host=OGMIOS_HOST,
    port=OGMIOS_PORT,
    network=Network.TESTNET
)

OGMIOS_POLL_SEC    =   1 # TODO does this matter? what's reasonable?
OGMIOS_TIMEOUT_SEC = 300

# Estimate of how long it might take a new TX to show up in the node.
# TODO how much longer should this be for production use?
# TODO rename network delay?
OGMIOS_DELAY_SEC = 10


### inital health check before running any testnet tests ###

async def ogmios_health() -> dict:
    url = f"http://{OGMIOS_HOST}:{OGMIOS_PORT}/health"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            resp.raise_for_status()
            health = await resp.json()
    return health

def ogmios_health_sync() -> dict:
    return asyncio.run(ogmios_health())


### get balances in order to track fees ###

def get_balance_ada(address: Address) -> float:
    """Return total lovelace balance at an address."""
    utxos = OGMIOS_CTX.utxos(address)
    balance_ll = sum(u.output.amount.coin for u in utxos)
    balance_ada = float(balance_ll) / LOVELACE_PER_ADA
    return balance_ada

# def get_balance_with_assets(ctx, address: Address):
#     """Return (lovelace, {policy_id: {asset_name: qty}})."""
#     utxos = ctx.utxos(address)
#     lovelace = 0
#     assets = {}
#     for u in utxos:
#         amt = u.output.amount
#         lovelace += amt.coin
#         if amt.multi_asset:
#             for pid, names in amt.multi_asset.items():
#                 bucket = assets.setdefault(pid, {})
#                 for name, qty in names.items():
#                     bucket[name] = bucket.get(name, 0) + qty
#     return lovelace, assets


### info for subscriber config ###

# TODO rename to make it more obvious this is for the --since args?
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

# TODO is this the only way we ever want to run it?
def query_network_tip_sync() -> dict:
    return asyncio.run(query_network_tip())


### fee calculations ###

# TODO remove if not using anywhere
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

def _other_outputs_coin(txb: "TransactionBuilder", out_utxo: TransactionOutput) -> int:
    """Sum of coin in every output except the continuation `out_utxo`."""
    return sum(o.amount.coin for o in txb.outputs if o is not out_utxo)


def _total_input_coin(txb: "TransactionBuilder") -> int:
    """Sum of coin across every spending input. Excludes collateral inputs,
    which don't enter the balance equation unless a script fails."""
    return sum(i.output.amount.coin for i in txb.inputs)

def _pointer(r: Redeemer) -> str:
    tag_str = {
        RedeemerTag.SPEND: "spend",
        RedeemerTag.MINT: "mint",
        RedeemerTag.CERTIFICATE: "certificate",
        RedeemerTag.WITHDRAWAL: "withdrawal",
    }[r.tag]
    return f"{tag_str}:{r.index}"

def _assign_spend_redeemer_indices(txb):
    sorted_inputs = sorted(
        txb.inputs,
        key=lambda u: (bytes(u.input.transaction_id), u.input.index),
    )
    for i, utxo in enumerate(sorted_inputs):
        r = txb._inputs_to_redeemers.get(utxo)
        if r is not None and r.tag in (None, RedeemerTag.SPEND):
            r.index = i

def evaluate_and_set_ex_units(
    txb: "TransactionBuilder",
    out_utxo: TransactionOutput,
) -> None:

    # Sanity: every script input must have its OWN Redeemer instance.
    seen = set()
    for utxo, r in txb._inputs_to_redeemers.items():
        assert id(r) not in seen, f"Redeemer instance shared across inputs: {utxo}"
        seen.add(id(r))

    _assign_spend_redeemer_indices(txb)

    # zero ex_units, seed fee/coin, then build
    for r in txb._redeemer_list:
        r.ex_units = ExecutionUnits(0, 0)
    total_in = _total_input_coin(txb)
    others   = _other_outputs_coin(txb, out_utxo)
    out_utxo.amount.coin = total_in - others - 200_000
    txb.fee = max_tx_fee(txb.context)

    tx_body = txb._build_tx_body()

    # Post-build invariant: unique (tag, index) per redeemer
    keys = [(r.tag, r.index) for r in txb._redeemer_list]
    assert len(keys) == len(set(keys)), f"Redeemer pointer collision: {keys}"

    draft_tx = Transaction(tx_body, txb.build_witness_set())
    result = txb.context.evaluate_tx(draft_tx)

    # Add a defensive assertion right before the pointer lookup so the failure
    # mode is loud and clear if a future PyCardano version changes when
    # tags/indices get assigned.
    for r in txb._redeemer_list:
        LOG.debug(f"redeemer tag={r.tag} index={r.index} data={r.data}")
        assert r.tag   is not None, f"Redeemer tag not set: {r}"
        assert r.index is not None, f"Redeemer index not set: {r}"
    LOG.debug(f"num script inputs: {len([i for i in txb.inputs if ...])}")

    mem_buf = 1.0 + txb.execution_memory_buffer
    step_buf = 1.0 + txb.execution_step_buffer
    for r in txb._redeemer_list:
        ptr = _pointer(r)
        if ptr not in result:
            raise RuntimeError(
                f"Ogmios did not return ex_units for redeemer {ptr}; "
                f"got keys {list(result.keys())}"
            )
        eu = result[ptr]
        r.ex_units = ExecutionUnits(
            mem=math.ceil(eu.mem * mem_buf),
            steps=math.ceil(eu.steps * step_buf),
        )


def set_out_value_and_fee(
    txb: "TransactionBuilder",
    out_utxo: TransactionOutput,
) -> None:
    """N-in / M-out: continuation output absorbs `Σ inputs − Σ others − fee`,
    iterating to a fixed point. Assumes redeemer ex_units are finalised and
    all other outputs have their final coin values set."""

    total_in = _total_input_coin(txb)
    others = _other_outputs_coin(txb, out_utxo)

    out_utxo.amount.coin = total_in - others   # realistic-size seed
    txb.fee = max_tx_fee(txb.context)

    prev_fee = None
    for _ in range(16):
        new_fee = txb._estimate_fee()
        if txb.fee_buffer:
            new_fee += txb.fee_buffer

        new_coin = total_in - others - new_fee
        min_lv = min_lovelace_post_alonzo(out_utxo, txb.context)
        if new_coin < min_lv:
            raise ValueError(
                f"Continuation under-funded: residual {new_coin} < min_ada "
                f"{min_lv} (in={total_in}, others={others}, fee={new_fee})"
            )

        txb.fee = new_fee
        out_utxo.amount.coin = new_coin
        if new_fee == prev_fee:
            break
        prev_fee = new_fee
    else:
        raise RuntimeError("Fee did not converge in 16 iterations")


### error handling ###


OGMIOS_FATAL_CODES = set({
})

OGMIOS_RETRY_CODES = set({
    3004,
    3010, # TODO is this really retryable?
    3110, # TODO is this really retryable?
})

OGMIOS_RETRY_PATTERNS = set({
    "unknown transaction input", # TODO is this really retryable?
    "missing from utxo set",     # TODO is this really retryable?
})

OGMIOS_SUCCESS_PATTERNS = set({
    "all inputs are spent",
    "probably already been included",
})


def ogmios_get_err_dict(e) -> dict | None:
    """Extract the Ogmios 'error' dict from a ResponseError."""
    LOG.debug(f'e: {type(e)} {e}')
    raw = str(e)  # works whether args[0] is str or something else
    LOG.debug(f'raw: {type(raw)} {raw}')
    prefix = "Ogmios responded with error: "
    idx = raw.find(prefix)
    LOG.debug(f'idx: {idx}')
    if idx == -1:
        return None
    try:
        full = ast.literal_eval(raw[idx + len(prefix):])
        LOG.debug(f'full: {full}')
    except (ValueError, SyntaxError):
        LOG.warning(f"Failed to parse Ogmios error dict from: {raw!r}")
        return None
    if isinstance(full, dict):
        return full.get("error")
    return None


def ogmios_extract_error_codes(e):
    """Extract all nested 'code' values from an Ogmios ResponseError."""
    codes = set()
    err = ogmios_get_err_dict(e)
    if err is None:
        LOG.error(f'err has no error codes')
        return set()
    def walk(node):
        if isinstance(node, dict):
            if "code" in node and isinstance(node["code"], int):
                codes.add(node["code"])
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    walk(err if isinstance(err, dict) else {})
    LOG.debug(f'Ogmios responded with error codes: {codes}')
    return codes


# def ogmios_extract_texts(e):
#     texts = set()
#     def walk(n):
#         if isinstance(n, dict):
#             for k, v in n.items():
#                 if k in ("error", "reason", "message") and isinstance(v, str):
#                     texts.add(v.lower())
#                 walk(v)
#         elif isinstance(n, list):
#             for v in n:
#                 walk(v)
#     walk(e)
#     return texts


def ogmios_classify_error(e):
    """Return one of: 'success', 'retry', 'fatal'."""
    # Parse error
    err = ogmios_get_err_dict(e)
    LOG.debug(f'err: {type(err)} {err}')
    if not isinstance(err, dict):
        LOG.error(f'ogmios error does not have an error dict. Assuming fatal: {e}')
        return "fatal"
    # Try to classify based on code first
    codes = ogmios_extract_error_codes(e)
    any_fatal_codes = codes & OGMIOS_FATAL_CODES
    any_retry_codes = codes & OGMIOS_RETRY_CODES
    LOG.debug(f'any_fatal_codes: {any_fatal_codes}')
    LOG.debug(f'any_retry_codes: {any_retry_codes}')
    if any_fatal_codes:
        return "fatal"
    if any_retry_codes:
        return "retry"
    # Then try based on text
    # texts = ogmios_extract_texts(e)
    # TODO make patterns regexes if the need comes up
    txt = str(e).lower() # Error is unstructured; might as well match on the whole thing
    any_success_text = any(p for p in OGMIOS_SUCCESS_PATTERNS if p in txt)
    any_retry_text   = any(p for p in OGMIOS_RETRY_PATTERNS   if p in txt)
    LOG.debug(f'any_success_text: {any_success_text}')
    LOG.debug(f'any_retry_text: {any_retry_text}')
    if any_success_text:
        return "success"
    if any_retry_text:
        return "retry"
    # Otherwise assume fatal
    LOG.error(f'ogmios error does not match a pattern. Assuming fatal: {e}')
    return "fatal"


def ogmios_retry(fn: Callable, timeout=OGMIOS_TIMEOUT_SEC) -> Optional[Any]:
    # Note that in case of "success" errors, we can't return a value.
    # That should be OK for our particular use cases.
    deadline = time.monotonic() + timeout
    attempt = 1
    while time.monotonic() < deadline:
        try:
            return fn()
        except ResponseError as e:
            verdict = ogmios_classify_error(e)
            LOG.debug(f'ogmios_retry attempt={attempt} verdict={verdict} e={e}')
            if verdict == "success":
                return
            if verdict == "retry":
                time.sleep(OGMIOS_DELAY_SEC)
                attempt += 1
                continue
            raise


### misc utils ###

def utxo_for_input(tx_in: TransactionInput) -> UTxO | None:
    tx_id_hex = tx_in.transaction_id.payload.hex()
    return OGMIOS_CTX.utxo_by_tx_id(tx_id_hex, tx_in.index)


def wait_for_confirmation_generic() -> int:
    "Wait long enough that any pending TXs should have confirmed."
    prev = None
    count = 0
    while count < 3:
        time.sleep(OGMIOS_POLL_SEC)
        tip = query_network_tip_sync()['block_hash']
        if tip == prev:
            continue
        elif prev is None:
            prev = tip
        else:
            count += 1
            LOG.debug(f'waited {count} blocks')
            prev = tip
    return


def is_utxo_unspent(utxo: UTxO) -> bool:
    """Return True if the given UTxO is still present on-chain (unspent)."""
    address = str(utxo.output.address)
    current = OGMIOS_CTX.utxos(address)
    return any(u.input == utxo.input for u in current)
