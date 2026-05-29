import json

from dataclasses import dataclass
from datetime import datetime
from functools import cached_property

from pycardano import Address, Network, TransactionInput, PlutusV3Script, ScriptHash

SCHEMA_VERSION = 1

@dataclass(frozen=True)
class ElectionScript:
    """The compiled, parameterized contract.

    Everything in here affects the script hash — change any field and you get
    a different on-chain contract. Network-independent: the same Script
    produces the same hash on mainnet and testnet.
    """

    # The input is used to construct the oneshot TX. The hex is the script parameter.
    # These are not duplicates of (reasonably accessible) info in the aiken_blueprint.
    # TODO later, make a list of params including token prefix below
    oneshot_input: TransactionInput
    oneshot_hex: str

    # The final JSON blueprint. Includes title, contract version, CBOR fields, etc.
    aiken_blueprint: dict

    # Fields duplicated from the aiken_blueprint for convenience.
    policy_id: ScriptHash
    mint_validator: PlutusV3Script
    spend_validator: PlutusV3Script

    # TODO later: git_commit
    # TODO later: token name prefix


@dataclass(frozen=True)
class ElectionDeployment:
    """Operational context for a particular deployment of an ElectionScript.

    None of these fields affect the script hash. The same Script can in
    principle be deployed with different Deployments (e.g. preprod then
    mainnet) and remain byte-identical.
    """

    # TODO later, distinguish preview from preprod
    network: Network

    # Useful if you want to quickly check who deployed it.
    # Also an informal default refund address for BurnTestTokens; not enforced on chain.
    funder_address: Address

    # So far, only used for picking the default JSON save path.
    deployment_date: datetime

    # The script-independent parts of the subscriber config.
    index_since_slot: int
    kupo_since_block_hash: str


@dataclass(frozen=True)
class Election:
    """Immutable record of a deployed election contract.

    Contains the compiled script, its parameters, and the deployment context
    needed to interact with it. Does NOT represent live on-chain state. To get that,
    you need to run a Verifier or other election role with an indexer.

    Things that change the script hash go in script; things that don't are part of
    deployment. Top level properties depend on both.
    """

    # This should be incremented whenever something changes that affects to/from_json.
    # Note that it's different from the contract version in the aiken_blueprint.
    schema_version: int

    script: ElectionScript
    deployment: ElectionDeployment

    @property
    def address(self) -> Address:
        """Script address, derived from the spend script hash and network."""
        # script_hash = PlutusV3Script(bytes.fromhex(self.script.spend_cbor_hex)).hash()
        # return Address(script_hash, network=self.deployment.network)
        ...

    # TODO to_dict / from_dict / to_json / from_json
