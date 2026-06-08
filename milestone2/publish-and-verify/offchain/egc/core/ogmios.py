# TODO rename node everywhere?

import asyncio
import json
import websockets
import time
from typing import Any, Dict

from pycardano import *

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
) -> TransactionId:
    """Plain wallet-to-wallet ADA send. Internal helper shared by the
    collateral funding / return / sweep functions. Not for spending from
    a script address."""
    builder = TransactionBuilder(OGMIOS_CTX)
    builder.add_input_address(sender.addr)
    builder.add_output(TransactionOutput(recipient, Value(lovelace)))
    signed = builder.build_and_sign([sender.sk], change_address=sender.addr)
    OGMIOS_CTX.submit_tx(signed)
    LOG.info(
        "Sent %d lovelace from %s to %s (tx %s)",
        lovelace, sender.addr, recipient, signed.id,
    )
    return signed.id


def create_own_collateral(funder: Wallet) -> TransactionId:
    """Op 1: Funder sends themselves exactly COLLATERAL_ADA to create a
    usable collateral UTXO. No-op (returns None-ish? see below) if one
    already exists — callers that want to force a new one should spend
    the existing one first."""
    existing = find_collateral_utxo(funder.addr)
    if existing is not None:
        LOG.info(
            "Collateral UTXO already exists at %s (%s#%d); skipping",
            funder.addr, existing.input.transaction_id, existing.input.index,
        )
        return existing.input.transaction_id
    LOG.info(f'Creating own collateral UTXO at {funder.addr}')
    return _send_ada(funder, funder.addr, COLLATERAL_LOVELACE)


def fund_admin_collateral(
    funder: Wallet,
    admin_address: Address,
) -> TransactionId:
    """Op 2 (standalone variant): Funder sends COLLATERAL_ADA to the
    admin address. In practice this is usually folded into the admin
    STT mint tx as an extra output — keep this around for tests and
    for the case where the admin needs a fresh collateral mid-election."""
    return _send_ada(funder, admin_address, COLLATERAL_LOVELACE)


def return_collateral(
    publisher: Wallet,
    funder_address: Address,
) -> TransactionId | None:
    """Op 5: Publisher voluntarily returns their collateral UTXO to the
    original funder. Convention, not enforced on-chain. Returns None if
    the publisher has no collateral UTXO to return."""
    utxo = find_collateral_utxo(publisher.wallet.addr)
    if utxo is None:
        LOG.info("No collateral UTXO at %s to return", publisher.wallet.addr)
        return None

    builder = TransactionBuilder(OGMIOS_CTX)
    builder.add_input(utxo)
    builder.add_output(TransactionOutput(funder_address, Value(COLLATERAL_LOVELACE)))
    signed = builder.build_and_sign(
        [publisher.wallet.sk], change_address=publisher.wallet.addr
    )
    OGMIOS_CTX.submit_tx(signed)
    LOG.info(
        "Returned collateral from %s to %s (tx %s)",
        publisher.wallet.addr, funder_address, signed.id,
    )
    return signed.id


def sweep_publisher_collateral(
    publisher: Wallet,
    funder_address: Address,
) -> TransactionId | None:
    """Op 6a: Per-publisher collateral sweep, signed by that publisher.
    Functionally identical to return_collateral right now; kept as a
    separate name because the cleanup script's semantics ("forcibly
    reclaim everything") may diverge from the voluntary-return
    semantics later (e.g., logging, error handling, batching across
    fixtures)."""
    return return_collateral(publisher, funder_address)
