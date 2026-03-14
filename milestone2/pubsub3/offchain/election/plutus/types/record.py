# Should be kept in sync with onchain/validators/election/record.ak

from .ipfs_cid import IpfsCid, IpfsCidHelper
from .channel import ChannelId
from dataclasses import dataclass
from pycardano import PlutusData
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
class BallotSubmitted(PlutusData):
    CONSTR_ID = 8
    ballot_id: bytes # TODO BallotId?

@dataclass
class CastNotice(PlutusData):
    CONSTR_ID = 9
    ballot_id: bytes # TODO BallotId?

@dataclass
class BallotSpoiled(PlutusData):
    CONSTR_ID = 10
    ballot_id: bytes # TODO BallotId?

@dataclass
class CiphertextTally(PlutusData):
    CONSTR_ID = 11

@dataclass
class TallyShare(PlutusData):
    CONSTR_ID = 12
    guardian_number: int

@dataclass
class SpoiledShare(PlutusData):
    CONSTR_ID = 13
    spoiled_id: bytes # TODO BallotId?
    guardian_number: int

@dataclass
class PlaintextTally(PlutusData):
    CONSTR_ID = 14

@dataclass
class SpoiledResult(PlutusData):
    CONSTR_ID = 15
    ballot_id: bytes # TODO BallotId?

@dataclass
class Summary(PlutusData):
    CONSTR_ID = 16
    verifier_id: ChannelId

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

@dataclass
class PublicRecord(PlutusData):
    CONSTR_ID = 0
    ipfs_cid: IpfsCid
    metadata: PublicRecordMetadata

    def __repr__(self):
        t = type(self.metadata).__name__
        c = IpfsCidHelper.to_string(self.cid)
        f"{t}(cid={c})"
