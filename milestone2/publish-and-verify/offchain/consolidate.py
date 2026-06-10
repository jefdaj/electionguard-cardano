#!/usr/bin/env python3

"""
Consolidate all UTXOs (ADA + native tokens) in a dev wallet into a single UTXO.
Reads signing key from dev.sk and address from dev.addr.
Uses a local Ogmios v6 instance for chain context.
"""

from pathlib import Path
from pycardano import (
    OgmiosV6ChainContext,
    Network,
    PaymentSigningKey,
    Address,
    TransactionBuilder,
)

# --- Config ---
OGMIOS_HOST = "localhost"
OGMIOS_PORT = 1337
NETWORK = Network.TESTNET  # preview is a testnet

SK_PATH   = Path("keys/dev.sk")
ADDR_PATH = Path("keys/dev.addr")

# Txs with native assets are larger per input than pure-ADA ones.
# Lower this if you hit tx-too-large errors.
MAX_INPUTS_PER_TX = 120


def load_wallet():
    skey = PaymentSigningKey.load(str(SK_PATH))
    addr = Address.from_primitive(ADDR_PATH.read_text().strip())
    return skey, addr


def summarize(utxos):
    total_lovelace = 0
    asset_count = 0
    policies = set()
    for u in utxos:
        total_lovelace += u.output.amount.coin
        ma = u.output.amount.multi_asset
        if ma:
            for pid, assets in ma.data.items():
                policies.add(pid)
                asset_count += len(assets)
    return total_lovelace, asset_count, len(policies)


def consolidate_batch(context, skey, addr, utxos):
    builder = TransactionBuilder(context)
    for u in utxos:
        builder.add_input(u)

    # With no explicit outputs and a change_address, the builder sweeps
    # everything (ADA + native assets) into a single output at `addr`,
    # automatically computing the fee and respecting min-ADA for the bundle.
    signed_tx = builder.build_and_sign(
        signing_keys=[skey],
        change_address=addr,
    )

    context.submit_tx(signed_tx)
    return signed_tx.id


def main():
    skey, addr = load_wallet()
    print(f"Wallet address: {addr}")

    context = OgmiosV6ChainContext(
        host=OGMIOS_HOST,
        port=OGMIOS_PORT,
        network=NETWORK,
    )

    utxos = context.utxos(str(addr))
    print(f"Found {len(utxos)} UTXOs at {addr}")

    if len(utxos) < 2:
        print("Nothing to consolidate (need at least 2 UTXOs).")
        return

    total_lovelace, asset_count, policy_count = summarize(utxos)
    print(f"Total: {total_lovelace / 1_000_000:.6f} tADA")
    print(f"Native assets: {asset_count} across {policy_count} policies")

    batches = [
        utxos[i : i + MAX_INPUTS_PER_TX]
        for i in range(0, len(utxos), MAX_INPUTS_PER_TX)
    ]
    print(f"Will need {len(batches)} transaction(s) total.")

    # Submit one batch per run so we don't try to spend UTXOs that haven't
    # made it on-chain yet. Re-run after confirmation to continue.
    batch = batches[0]
    print(f"\nSubmitting batch of {len(batch)} inputs...")
    try:
        tx_id = consolidate_batch(context, skey, addr, batch)
        print(f"  tx submitted: {tx_id}")
    except Exception as e:
        print(f"  submission failed: {e}")
        print("  If this is a tx-size error, lower MAX_INPUTS_PER_TX and retry.")
        raise

    if len(batches) > 1:
        print(
            f"\n{len(batches) - 1} more batch(es) remaining. "
            f"Wait ~30–60s for confirmation, then re-run."
        )
    else:
        print("\nAll done after this confirms!")


if __name__ == "__main__":
    main()
