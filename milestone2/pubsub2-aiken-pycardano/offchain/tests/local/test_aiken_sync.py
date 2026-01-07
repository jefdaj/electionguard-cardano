# Makes sure the Python code stays in sync with Aiken definitions

import json
from pathlib import Path
from pubsub.types.datums import ChannelDatum

def test_channel_datum_matches_plutus_json():
    """Ensure Python types match the compiled Aiken output."""
    plutus_json = Path("../onchain/plutus.json") # TODO does this work with relative paths? sick...
    
    if not plutus_json.exists():
        pytest.skip("Run 'aiken build' first")
    
    with open(plutus_json) as f:
        schema = json.load(f)
    
    # Extract the datum schema for your validator
    validator = schema["validators"][0]  # Adjust index as needed
    datum_schema = validator["datum"]["schema"]
    
    # Verify structure matches
    assert datum_schema["$comment"] == "ChannelDatum"
    # Add more specific checks based on your schema
