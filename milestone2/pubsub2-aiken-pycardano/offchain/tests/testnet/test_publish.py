import pytest
from pubsub.types import ChannelDatum
from pubsub.builders import build_publish_tx

@pytest.mark.integration
@pytest.mark.slow
def test_publish_channel_to_preview(chain_context, publisher_key, funded_address):
    """End-to-end test: publish a channel datum to Preview testnet."""
    # Create datum
    datum = ChannelDatum(
    owner=publisher_key.to_verification_key().hash().payload,
        cids=[b"QmTest123"]
    )
    # Build transaction
    builder = build_publish_tx(
        context=chain_context,
        publisher_address=funded_address,
        channel_datum=datum,
        validator_address="addr_test...",  # Your deployed validator
        collateral_utxo=None  # Select from funded_address
    )
    # Sign and submit
    signed_tx = builder.build_and_sign([publisher_key], change_address=funded_address)
    tx_hash = chain_context.submit_tx(signed_tx)
    # Wait for confirmation
    chain_context.wait_for_tx(tx_hash, timeout=120)
    # Verify the datum is on-chain
    validator_utxos = chain_context.utxos("addr_test...")  # validator address
    found_datum = any(
        utxo.output.datum == datum 
        for utxo in validator_utxos
    )
    assert found_datum, "Datum not found at validator address"

