import json
import logging

LOG = logging.getLogger(__name__)

from dataclasses import dataclass, field
from datetime import datetime
from functools import cached_property
from pathlib import Path
from typing import Self
from pprint import pformat

from pycardano import *

from .plutus import *

import logging

LOG = logging.getLogger(__name__)

SCHEMA_VERSION = 2

@dataclass(frozen=True, kw_only=True)
class ElectionScript:
    """The compiled, parameterized contract.

    Network-independent: the same Script produces the same hash on mainnet and testnet.
    """

    # The input is used to construct the oneshot TX. The hex is the script parameter.
    # These are not duplicates of (reasonably accessible) info in the aiken_blueprint.
    # TODO Is there a less awkward method than utxo as cbor_hex that's still reliable?
    # TODO later, make a list of params including token prefix below
    oneshot_utxo: UTxO
    oneshot_hex: str

    # The final JSON blueprint. Includes title, contract version, CBOR fields, etc.
    aiken_blueprint: dict

    # Was the contract built with tracing?
    # Example usage with tracing:
    # ELECTION_PLUTUS_VARIANT=traced ./publish.py ...
    aiken_tracing: bool = field(default=USE_TRACED)

    # Fields duplicated from the aiken_blueprint for convenience.
    policy_id:    ScriptHash
    mint_script:  PlutusV3Script
    spend_script: PlutusV3Script

    # TODO later: git_commit
    # TODO later: token name prefix

    def to_dict(self) -> dict:
        LOG.debug('ElectionScript.to_dict')
        return {
            "oneshot_utxo": self.oneshot_utxo.to_cbor_hex(),
            "oneshot_hex": self.oneshot_hex,
            "aiken_blueprint": self.aiken_blueprint,
            "aiken_tracing": self.aiken_tracing,
        }

    # TODO is this a reasonable way to initially create it, with a round-trip to json?
    @classmethod
    def from_oneshot_utxo(cls, oneshot_utxo: UTxO) -> Self:
        oneshot_hex = utxo_to_ref_hex(oneshot_utxo)
        hex_params = [oneshot_hex]
        blueprint_dict = aiken_blueprint_apply_hex_params(PLUTUS_JSON_PATH, hex_params)
        cls_dict = {
            'schema_version': SCHEMA_VERSION,
            'oneshot_utxo': oneshot_utxo.to_cbor_hex(),
            'oneshot_hex': oneshot_hex,
            'aiken_blueprint': blueprint_dict,
            "aiken_tracing": USE_TRACED,
        }
        return cls.from_dict(cls_dict)

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        LOG.debug('ElectionScript.from_dict')
        oneshot_utxo = UTxO.from_cbor(bytes.fromhex(data["oneshot_utxo"]))
        blueprint = data["aiken_blueprint"]
        mint_dict  = next(v for v in blueprint["validators"] if 'mint'  in v['title'])
        spend_dict = next(v for v in blueprint["validators"] if 'spend' in v['title'])
        mint_script  = PlutusV3Script(bytes.fromhex(  mint_dict["compiledCode"] ))
        spend_script = PlutusV3Script(bytes.fromhex( spend_dict["compiledCode"] ))
        policy_id = plutus_script_hash(mint_script)
        return cls(
            oneshot_utxo    = oneshot_utxo,
            oneshot_hex     = data["oneshot_hex"],
            aiken_blueprint = blueprint,
            aiken_tracing   = data["aiken_tracing"],
            policy_id       = policy_id,
            mint_script     = mint_script,
            spend_script    = spend_script,
        )

@dataclass(frozen=True)
class ElectionDeployment:
    """Operational context for a particular deployment of an ElectionScript.

    None of these fields affect the script hash.
    """

    # TODO later, distinguish preview from preprod
    network: Network

    # Useful if you want to quickly check who deployed it.
    # Also an informal default refund address for BurnTestTokens; not enforced on chain.
    funder_address: Address

    # So far, only used for picking the default JSON save path.
    deployment_date: datetime

    # The script-independent parts of the subscriber config.
    index_from_slot: int
    index_from_block_hash: str

    def to_dict(self) -> dict:
        LOG.debug('ElectionDeployment.to_dict')
        return {
            "network":               self.network.name.lower(),  # "mainnet" / "testnet"
            "funder_address":        str(self.funder_address),
            "deployment_date":       self.deployment_date.isoformat(),
            "index_from_slot":      self.index_from_slot,
            "index_from_block_hash": self.index_from_block_hash,
        }


    @classmethod
    def from_dict(cls, data: dict) -> Self:
        LOG.debug('ElectionDeployment.from_dict')
        return cls(
            network               = Network[data["network"].upper()],
            funder_address        = Address.from_primitive(data["funder_address"]),
            deployment_date       = datetime.fromisoformat(data["deployment_date"]),
            index_from_slot       = data["index_from_slot"],
            index_from_block_hash = data["index_from_block_hash"],
        )

@dataclass(frozen=True, kw_only=True)
class ElectionContext:
    """Immutable record of a deployed election contract.

    Contains the compiled script, its parameters, and the deployment context
    needed to interact with it. Does NOT represent live on-chain state. To get that,
    you need to run a Verifier or other election role with an indexer.

    Things that change the script hash go in script; things that don't are part of
    deployment. Top level properties depend on both.
    """

    # This should be incremented whenever something changes that affects to/from_json.
    # Note that it's different from the contract version in the aiken_blueprint.
    schema_version: int = field(default=SCHEMA_VERSION)

    script: ElectionScript
    deployment: ElectionDeployment

    @property
    def address(self) -> Address:
        """Script address, derived from the spend script hash and network."""
        LOG.debug('Election.address')
        # TODO can policy_id be used directly?
        return Address(self.script.policy_id, network=self.deployment.network)

    def to_dict(self) -> dict:
        LOG.debug('Election.to_dict')
        return {
            "schema_version": self.schema_version,
            "script":         self.script.to_dict(),
            "deployment":     self.deployment.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        LOG.debug('Election.from_dict')
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
        LOG.debug('Election.to_json')
        Path(path).write_text(json.dumps(self.to_dict(), indent=2))
        LOG.debug(f'saved ElectionContext to {path}')

    @classmethod
    def from_json(cls, path: str | Path) -> Self:
        LOG.debug('Election.from_json')
        obj = cls.from_dict(json.loads(Path(path).read_text()))
        LOG.debug(f'loaded ElectionContext from {path}')
        return obj
