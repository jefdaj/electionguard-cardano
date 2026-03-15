# Should be kept in sync with onchain/validators/election/types/record.ak

from .ballot_id import BallotIdMixin
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
class Constants(PlutusData):
    CONSTR_ID = 6

@dataclass
class Device(PlutusData):
    CONSTR_ID = 7
    device_number: int

@dataclass
class BallotSubmitted(BallotIdMixin, PlutusData):
    CONSTR_ID = 8
    ballot_id: bytes

@dataclass
class CastNotice(BallotIdMixin, PlutusData):
    CONSTR_ID = 9
    ballot_id: bytes

@dataclass
class BallotSpoiled(BallotIdMixin, PlutusData):
    CONSTR_ID = 10
    ballot_id: bytes

@dataclass
class CiphertextTally(PlutusData):
    CONSTR_ID = 11

@dataclass
class TallyShare(PlutusData):
    CONSTR_ID = 12
    guardian_number: int

@dataclass
class SpoiledShare(BallotIdMixin, PlutusData):
    CONSTR_ID = 13
    spoiled_id: bytes # TODO same ballot- prefix, right?
    guardian_number: int

@dataclass
class PlaintextTally(PlutusData):
    CONSTR_ID = 14

@dataclass
class SpoiledResult(BallotIdMixin, PlutusData):
    CONSTR_ID = 15
    ballot_id: bytes

@dataclass
class Summary(ChannelIdMixin, PlutusData):
    CONSTR_ID = 16
    verifier_id: bytes

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

# TODO metadata mixin?
@dataclass
class PublicRecord(IpfsCidMixin, PlutusData):
    CONSTR_ID = 0
    ipfs_cid: bytes
    metadata: PublicRecordMetadata

    def __repr__(self):
        m = type(self.metadata).__name__ + '()'
        c = IpfsCidHelper.to_string(self.ipfs_cid)
        return f"PublicRecord(ipfs_cid={c}, metadata={m})"
