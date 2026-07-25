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

from .env import EGC_PLUTUS_MODE, EGC_NETWORK_MODE
from .plutus import *
# from .subscriber import ElectionConfig

import logging

LOG = logging.getLogger(__name__)

# Increment whenever you change the serialization.
SCHEMA_VERSION = 3

NETWORK_MAGIC = {
    "mainnet": 764824073,
    "preprod": 1,
    "preview": 2,
}

PYCARDANO_NETWORK = {
    764824073: Network.MAINNET,
    1: Network.TESTNET,
    2: Network.TESTNET,
}

DEFAULT_NETWORK_MAGIC     = NETWORK_MAGIC[EGC_NETWORK_MODE]
DEFAULT_PYCARDANO_NETWORK = PYCARDANO_NETWORK[DEFAULT_NETWORK_MAGIC]


@dataclass
class ElectionConfig:

    # the one-shot utxo script parameter
    oneshot_hex: str

    # which network was it deployed on?
    network_magic: int

    # for returning collateral
    # May also be helpful to confirm it's a known treasury address when you're
    # hearing about a new election?
    # TODO should this only be the vkh, and Address is derived from that + network?
    funder_address: str

    # TODO remove and re-derive from utxo above
    # policy_id:   str # For kupo --match

    # for kupo --since
    since_slot:  int
    since_block: str

    schema_version: int = field(default=SCHEMA_VERSION)

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return cls(
                data['oneshot_hex'   ],
            int(data['network_magic' ]),
            str(data['funder_address']),
            int(data['since_slot'    ]),
                data['since_block'   ],
                data['schema_version'],
        )

    # TODO is this right?
    @classmethod
    def from_json(cls, data: str) -> Self:
        return cls.from_dict(
            json.loads(data)
        )

    # TODO is this str typing thing right?
    @classmethod
    def from_election(cls, election: "ElectionContext") -> Self:
        return cls(
            election.script.oneshot_hex,
            election.deployment.network_magic,
            str(election.deployment.funder_address),
            election.deployment.since_slot,
            election.deployment.since_block,
            election.schema_version,
        )

    @classmethod
    def from_qr_str(cls, txt: str) -> Self:
        "egc:election:<version>:<onshot_hex>:<network_magic>:<funder_address>:<since_slot>:<since_block>, maybe with wrapping"
        txt = ''.join(l.strip() for l in txt.splitlines())
        print(f'from_qr_str txt: {txt}')
        words = txt.split(':')
        prefix = words[:2]
        args   = words[2:]
        assert prefix == ['egc', 'election']
        assert len(args) == 6
        schema_version, oneshot_hex, network_magic, funder_address, since_slot, since_block = args
        since_slot = int(since_slot)
        funder_address = str(funder_address)
        return cls(oneshot_hex, network_magic, funder_address, since_slot, since_block, schema_version)

    def to_qr_str(self) -> str:
        "egc:election:<version>:<oneshot_hex>:<network_magic>:<funder_address>:<since_slot>:<since_block>"
        qr_str = ':'.join([
            'egc', 'election',
            str(self.schema_version), # TODO put last?
            self.oneshot_hex,
            str(self.network_magic),
            str(self.funder_address),
            str(self.since_slot),
            self.since_block
        ])
        return qr_str


# TODO where should this live?
def derive_script(oneshot_utxo: UTxO):
    oneshot_hex = utxo_to_ref_hex(oneshot_utxo)
    script = ElectionScript.from_oneshot_hex(oneshot_hex)
    return script
 

@dataclass(frozen=True, kw_only=True)
class ElectionScript:
    """The compiled, parameterized contract.

    Network-independent: the same Script produces the same hash on mainnet and testnet.
    """

    # The input is used to construct the oneshot TX. The hex is the script parameter.
    # These are not duplicates of (reasonably accessible) info in the aiken_blueprint.
    # TODO Is there a less awkward method than utxo as cbor_hex that's still reliable?
    # TODO later, make a list of params including token prefix below
    # oneshot_utxo: UTxO # TODO is this needed anymore?
    oneshot_hex: str

    # The final JSON blueprint. Includes title, contract version, CBOR fields, etc.
    aiken_blueprint: dict

    # Was the contract built with tracing?
    # Example usage with tracing:
    # ELECTION_PLUTUS_VARIANT=traced ./publish.py ...
    aiken_tracing: bool = field(default='traced' in EGC_PLUTUS_MODE)

    # Fields duplicated from the aiken_blueprint for convenience.
    policy_id:    ScriptHash
    mint_script:  PlutusV3Script
    spend_script: PlutusV3Script

    # TODO later: git_commit
    # TODO later: token name prefix

    def to_dict(self) -> dict:
        LOG.debug('ElectionScript.to_dict')
        return {
                # "oneshot_utxo": self.oneshot_utxo.to_cbor_hex(),
            "oneshot_hex":     self.oneshot_hex,
            "aiken_blueprint": self.aiken_blueprint,
            "aiken_tracing":   self.aiken_tracing,
        }

    # TODO is this just __init__?
    @classmethod
    def from_oneshot_hex(cls, oneshot_hex: str) -> Self:
        hex_params = [oneshot_hex]
        blueprint_dict = aiken_blueprint_apply_hex_params(PLUTUS_JSON_PATH, hex_params)
        cls_dict = {
            # 'schema_version':  SCHEMA_VERSION,
            'oneshot_hex':     oneshot_hex,
            'aiken_blueprint': blueprint_dict,
            "aiken_tracing":   'traced' in EGC_PLUTUS_MODE,
        }
        return cls.from_dict(cls_dict)

    @classmethod
    def from_config(cls, cfg: ElectionConfig) -> Self:
        # oneshot_hex = utxo_to_ref_hex(oneshot_utxo)
        hex_params = [cfg.oneshot_hex]
        blueprint_dict = aiken_blueprint_apply_hex_params(PLUTUS_JSON_PATH, hex_params)
        cls_dict = {
            # 'schema_version': SCHEMA_VERSION,
            # 'oneshot_utxo': oneshot_utxo.to_cbor_hex(),
            'oneshot_hex': cfg.oneshot_hex,
            'aiken_blueprint': blueprint_dict,
            "aiken_tracing": 'traced' in EGC_PLUTUS_MODE,
        }
        return cls.from_dict(cls_dict)


    @classmethod
    def from_dict(cls, data: dict) -> Self:
        LOG.debug('ElectionScript.from_dict')
        # oneshot_utxo = UTxO.from_cbor(bytes.fromhex(data["oneshot_utxo"]))
        blueprint = data["aiken_blueprint"]
        mint_dict  = next(v for v in blueprint["validators"] if 'mint'  in v['title'])
        spend_dict = next(v for v in blueprint["validators"] if 'spend' in v['title'])
        mint_script  = PlutusV3Script(bytes.fromhex(  mint_dict["compiledCode"] ))
        spend_script = PlutusV3Script(bytes.fromhex( spend_dict["compiledCode"] ))
        policy_id = plutus_script_hash(mint_script)
        return cls(
                # oneshot_utxo    = oneshot_utxo,
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

    # Useful if you want to quickly check who deployed it.
    # Also an informal default refund address for BurnTestTokens; not enforced on chain.
    # TODO for now, also include in subscriber info qrcode
    funder_address: str # Address

    # So far, only used for picking the default JSON save path.
    # TODO remove? slot_no is probably better
    # deployment_date: datetime

    # The script-independent parts of the subscriber config.
    since_slot: int
    since_block: str

    network_magic: int = field(default=DEFAULT_NETWORK_MAGIC)

    @classmethod
    def from_config(cls, cfg: ElectionConfig) -> Self:
        cls_dict = {
            'funder_address': str(cfg.funder_address),
            'since_slot':     int(cfg.since_slot    ),
            'since_block':    str(cfg.since_block   ),
            'network_magic':  int(cfg.network_magic ),
        }
        return cls.from_dict(cls_dict)

    def to_dict(self) -> dict:
        LOG.debug('ElectionDeployment.to_dict')
        return {
            "funder_address": str(self.funder_address),
            "since_slot":     int(self.since_slot    ),
            "since_block":    str(self.since_block   ),
            "network_magic":  int(self.network_magic ),
        }


    @classmethod
    def from_dict(cls, data: dict) -> Self:
        LOG.debug('ElectionDeployment.from_dict')
        return cls(
            funder_address = str(data["funder_address"]),
            since_slot     = int(data["since_slot"    ]),
            since_block    = str(data["since_block"   ]),
            network_magic  = int(data["network_magic" ]),
        )

# TODO rename something better?
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

    deployment: ElectionDeployment
    script: ElectionScript

    @property
    def address(self) -> Address:
        """Script address, derived from the spend script hash and network."""
        LOG.debug('Election.address')
        return Address(
            self.script.policy_id,
            network=PYCARDANO_NETWORK[self.deployment.network_magic],
        )

    def to_dict(self) -> dict:
        LOG.debug('Election.to_dict')
        return {
            "schema_version": self.schema_version,
            "deployment":     self.deployment.to_dict(),
            "script":         self.script.to_dict(),
        }

    @classmethod
    def from_config(cls, cfg: ElectionConfig) -> Self:
        deployment = ElectionDeployment.from_config(cfg)
        script     = ElectionScript.from_config(cfg)
        return cls(
            schema_version = SCHEMA_VERSION, # TODO get from qrcode
            deployment     = deployment,
            script         = script,
        )

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
            deployment     = ElectionDeployment.from_dict(data["deployment"]),
            script         = ElectionScript.from_dict(data["script"]),
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
