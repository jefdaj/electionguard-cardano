# TODO rename node everywhere?

import asyncio
import json
import websockets
import time
import math
from typing import Any, Dict, Optional

from pycardano import *
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

OGMIOS_POLL_SEC    =   3.0
OGMIOS_TIMEOUT_SEC = 300.0

# Estimate of how long it might take a new TX to show up in the node.
# TODO how much longer should this be for production use?
OGMIOS_DELAY_SEC = 3.0

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


def evaluate_and_set_ex_units(
    txb: "TransactionBuilder",
    out_utxo: TransactionOutput,
    redeemers: list[Redeemer],
) -> None:
    """Evaluate ex_units via Ogmios and write results back to each redeemer.

    Seeds `out_utxo.coin` and `txb.fee` with plausible values so the draft
    tx's CBOR size matches the final tx (script context cost depends on it).
    """
    STUB_FEE = 200_000
    total_in = _total_input_coin(txb)
    others = _other_outputs_coin(txb, out_utxo)

    out_utxo.amount.coin = total_in - others - STUB_FEE
    txb.fee = max_tx_fee(txb.context)

    for r in redeemers:
        r.ex_units = ExecutionUnits(mem=0, steps=0)

    draft_tx = Transaction(
        transaction_body=txb._build_tx_body(),
        transaction_witness_set=txb.build_witness_set(),
    )
    result: Dict[str, ExecutionUnits] = txb.context.evaluate_tx(draft_tx)

    def _pointer(r: Redeemer) -> str:
        tag_str = {
            RedeemerTag.SPEND: "spend",
            RedeemerTag.MINT: "mint",
            RedeemerTag.CERTIFICATE: "certificate",
            RedeemerTag.WITHDRAWAL: "withdrawal",
        }[r.tag]
        return f"{tag_str}:{r.index}"

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


### collateral operations ###

def find_collateral_utxo(address: Address) -> UTxO | None:
    """Return a collateral-eligible UTXO at `address`, or None.

    "Collateral-eligible" means: exactly COLLATERAL_LOVELACE lovelace,
    no native assets, no datum, no script ref. This is stricter than
    the ledger requires, but it guarantees the UTXO matches what our
    funding functions produce and won't collide with other holdings.
    """
    utxos = OGMIOS_CTX.utxos(address)
    for utxo in utxos:
        amt = utxo.output.amount
        if amt.coin != COLLATERAL_LOVELACE:
            continue
        if amt.multi_asset and len(amt.multi_asset) > 0:
            continue
        if utxo.output.datum is not None:
            continue
        if utxo.output.datum_hash is not None:
            continue
        if utxo.output.script is not None:
            continue
        return utxo
    return None


def get_my_collateral(address: Address) -> UTxO:
    """Like find_collateral_utxo but raises if missing. Publishers call
    this when building any contract tx and pass the result as the
    collateral input."""
    utxo = find_collateral_utxo(address)
    if utxo is None:
        raise RuntimeError(
            f"No collateral UTXO ({COLLATERAL_ADA} ADA, no assets, no datum) "
            f"found at {address}. Run create_own_collateral or ask the "
            f"funder to send one."
        )
    return utxo


# TODO unify with wait_for_confirmation?
def wait_for_collateral(address: Address) -> UTxO:
    """Poll for a collateral UTXO at `address` until one appears or
    OGMIOS_TIMEOUT_SEC elapses. Used right after a funding tx to bridge
    the gap between submission and the publisher's address being
    re-indexed."""
    deadline = time.monotonic() + OGMIOS_TIMEOUT_SEC
    while True:
        utxo = find_collateral_utxo(address)
        if utxo is not None:
            return utxo
        if time.monotonic() >= deadline:
            raise TimeoutError(
                f"Collateral UTXO did not appear at {address} within "
                f"{OGMIOS_TIMEOUT_SEC}s"
            )
        time.sleep(OGMIOS_POLL_SEC)


def _send_ada(
    sender: Wallet,
    recipient: Address,
    lovelace: int,
) -> Transaction:
    """Plain wallet-to-wallet ADA send. Internal helper shared by the
    collateral funding / return / sweep functions. Not for spending from
    a script address."""
    builder = TransactionBuilder(OGMIOS_CTX)
    builder.add_input_address(sender.addr)
    builder.add_output(TransactionOutput(recipient, Value(lovelace)))
    signed = builder.build_and_sign([sender.sk], change_address=sender.addr)
    OGMIOS_CTX.submit_tx(signed)
    LOG.debug(
        "Sent %d lovelace from %s to %s (tx %s)",
        lovelace, sender.addr, recipient, signed.id,
    )
    return signed


def create_own_collateral(funder: Wallet) -> Transaction:
    """Op 1: Funder sends themselves exactly COLLATERAL_ADA to create a
    usable collateral UTXO. No-op (returns None-ish? see below) if one
    already exists — callers that want to force a new one should spend
    the existing one first."""
    existing = find_collateral_utxo(funder.addr)
    if existing is not None:
        LOG.debug(
            "Collateral UTXO already exists at %s (%s#%d); skipping",
            funder.addr, existing.input.transaction_id, existing.input.index,
        )
        return existing.input.transaction_id
    res = _send_ada(funder, funder.addr, COLLATERAL_LOVELACE)
    LOG.info(f'Created own collateral UTXO at {funder.addr}')
    return res


def fund_admin_collateral(
    funder: Wallet,
    admin_address: Address,
) -> Transaction:
    """Op 2 (standalone variant): Funder sends COLLATERAL_ADA to the
    admin address. In practice this is usually folded into the admin
    STT mint tx as an extra output — keep this around for tests and
    for the case where the admin needs a fresh collateral mid-election."""
    return _send_ada(funder, admin_address, COLLATERAL_LOVELACE)


def return_collateral(
    publisher_wallet: Wallet,
    funder_address: Address,
) -> Optional[TransactionId]:
    """Op 5: Publisher voluntarily returns their collateral UTXO to the
    original funder, less tx fee. The publisher is expected to do this,
    but it can't be enforced on chain. Returns None if the publisher has
    no collateral UTXO to return."""
    utxo = find_collateral_utxo(publisher_wallet.addr)
    if utxo is None:
        LOG.debug("No collateral UTXO at %s to return", publisher_wallet.addr)
        return None
    builder = TransactionBuilder(OGMIOS_CTX)
    builder.add_input(utxo)
    # No add_output / no change_address pointing at publisher — we want
    # the entire UTXO to go to the funder, minus the fee. Using the
    # funder as the change address makes the builder route the remainder
    # (collateral - fee) to them automatically.
    signed = builder.build_and_sign(
        [publisher_wallet.sk], change_address=funder_address,
    )
    OGMIOS_CTX.submit_tx(signed)
    LOG.debug(
        "Returned collateral from %s to %s, less tx fee (tx %s)",
        publisher_wallet.addr, funder_address, signed.id,
    )
    return signed
