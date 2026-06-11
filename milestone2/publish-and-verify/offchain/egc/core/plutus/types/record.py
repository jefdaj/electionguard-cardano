# Should be kept in sync with onchain/validators/election/types/record.ak

from .ballot_id import BallotId, BallotIdMixin
from .channel_id import ChannelIdMixin
from .ipfs_cid import IpfsCidHelper, IpfsCidMixin
from dataclasses import dataclass
from pycardano import PlutusData
from pydantic.v1 import validator
from typing import Union

@dataclass
class Manifest(PlutusData):
    CONSTR_ID = 0

@dataclass
class CeremonyDetails(PlutusData):
    CONSTR_ID = 1

@dataclass
class GuardianPubkey(PlutusData):
    CONSTR_ID = 2
    guardian_number: int

@dataclass
class GuardianBackup(PlutusData):
    CONSTR_ID = 3
    guardian_number: int
    backup_order: int

@dataclass
class GuardianVerification(PlutusData):
    CONSTR_ID = 4
    guardian_number: int
    backup_order: int

@dataclass
class JointKey(PlutusData):
    CONSTR_ID = 5

@dataclass
class Context(PlutusData):
    CONSTR_ID = 6

@dataclass
class Constants(PlutusData):
    CONSTR_ID = 7

@dataclass
class Device(PlutusData):
    CONSTR_ID = 8
    device_number: int

@dataclass
class BallotSubmitted(BallotIdMixin, PlutusData):
    CONSTR_ID = 9
    ballot_id: BallotId

@dataclass
class CastNotice(BallotIdMixin, PlutusData):
    CONSTR_ID = 10
    ballot_id: BallotId

@dataclass
class BallotSpoiled(BallotIdMixin, PlutusData):
    CONSTR_ID = 11
    ballot_id: BallotId

@dataclass
class CiphertextTally(PlutusData):
    CONSTR_ID = 12

@dataclass
class TallyShare(PlutusData):
    CONSTR_ID = 13
    guardian_number: int

@dataclass
class SpoiledShare(BallotIdMixin, PlutusData):
    CONSTR_ID = 14
    spoiled_id: BallotId # TODO same ballot- prefix, right?
    guardian_number: int

@dataclass
class PlaintextTally(PlutusData):
    CONSTR_ID = 15

@dataclass
class SpoiledResult(BallotIdMixin, PlutusData):
    CONSTR_ID = 16
    ballot_id: BallotId

@dataclass
class Summary(ChannelIdMixin, PlutusData):
    CONSTR_ID = 17
    verifier_id: BallotId

PublicRecordMetadata = Union[
    Manifest,
    CeremonyDetails,
    GuardianPubkey,
    GuardianBackup,
    GuardianVerification,
    JointKey,
    Constants,
    Device,
    BallotSubmitted,
    CastNotice,
    BallotSpoiled,
    CiphertextTally,
    TallyShare,
    SpoiledShare,
    PlaintextTally,
    SpoiledResult,
    Summary,
]

@dataclass(repr=False)
class PublicRecord(IpfsCidMixin, PlutusData):
    CONSTR_ID = 0
    ipfs_cid: bytes
    metadata: PublicRecordMetadata
