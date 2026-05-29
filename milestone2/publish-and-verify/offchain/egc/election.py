import json

from dataclasses import dataclass
from datetime import datetime
from functools import cached_property
from pathlib import Path
from typing import Self

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
    policy_id:    ScriptHash
    mint_script:  PlutusV3Script
    spend_script: PlutusV3Script

    # TODO later: git_commit
    # TODO later: token name prefix

    def to_dict(self) -> dict:
        return {
            "oneshot_input": {
                "tx_id": str(self.oneshot_input.transaction_id),
                "output_index": self.oneshot_input.index,
            },
            "oneshot_hex": self.oneshot_hex,
            "aiken_blueprint": self.aiken_blueprint,
            # policy_id, mint_script, spend_script will be rederived from blueprint
        }

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        oneshot_input = TransactionInput(
            TransactionId(bytes.fromhex(data["oneshot_input"]["tx_id"])),
            data["oneshot_input"]["output_index"],
        )
        blueprint = data["aiken_blueprint"]
        mint_dict  = next(v for v in data["validators"] if 'mint'  in v['title'])
        spend_dict = next(v for v in data["validators"] if 'spend' in v['title'])
        mint_script  = PlutusV3Script(bytes.fromhex(  mint_dict["compiledCode"] ))
        spend_script = PlutusV3Script(bytes.fromhex( spend_dict["compiledCode"] ))

        # extra check to be sure that my apply_params hack isn't breaking anything
        rederived = ScriptHash(bytes.fromhex(mint_validator["hash"]))
        from_blueprint = mint_script.hash()
        if from_blueprint != rederived:
            raise ValueError(
                f"Blueprint inconsistency: compiledCode hashes to {rederived}, "
                f"but blueprint claims {from_blueprint}. May have an apply_params bug."
            )

        return cls(
            oneshot_input   = oneshot_input,
            oneshot_hex     = data["oneshot_hex"],
            aiken_blueprint = blueprint,
            policy_id       = from_blueprint,
            mint_script     = mint_script,
            spend_script    = spend_script,
        )

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

    def to_dict(self) -> dict:
        return {
            "network":               self.network.name.lower(),  # "mainnet" / "testnet"
            "funder_address":        str(self.funder_address),
            "deployment_date":       self.deployment_date.isoformat(),
            "index_since_slot":      self.index_since_slot,
            "kupo_since_block_hash": self.kupo_since_block_hash,
        }


    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return cls(
            network               = Network[data["network"].upper()],
            funder_address        = Address.from_primitive(data["funder_address"]),
            deployment_date       = datetime.fromisoformat(data["deployment_date"]),
            index_since_slot      = data["index_since_slot"],
            kupo_since_block_hash = data["kupo_since_block_hash"],
        )

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


    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "script":         self.script.to_dict(),
            "deployment":     self.deployment.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        version = data.get("schema_version")
        if version != SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported schema version: {version!r} "
                f"(this code expects {SCHEMA_VERSION})"
            )
        return cls(
            schema_version = version,
            script         = ElectionScript.from_dict(data["script"]),
            deployment     = ElectionDeployment.from_dict(data["deployment"]),
        )

    def to_json(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def from_json(cls, path: str | Path) -> Self:
        return cls.from_dict(json.loads(Path(path).read_text()))
