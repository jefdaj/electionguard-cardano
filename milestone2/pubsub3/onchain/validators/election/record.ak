use aiken/collection/list

use election/cid.{CIDv1, validate_cid}
use election/ballot_id.{validate_ballot_id}

// These aren't part of the ElectionGuard protocol as far as I know,
// but it seems reasonable to err on the side of safety for now.
// I've run elections with up to 99 guardians in the Python code.
const max_guardians: Int = 100
const max_devices  : Int = 100
const max_verifiers: Int = 100

pub type PublicRecordMetadata {
  Manifest
  CeremonyDetails
  GuardianPubkey {
    guardian_number: Int,
  }
  GuardianBackup {
    guardian_number: Int,
    backup_order: Int
  }
  GuardianVerification {
    guardian_number: Int,
    backup_order: Int
  }
  JointKey
  Constants
  Device {
    device_number: Int
  }
  BallotSubmitted {
    ballot_id: ByteArray
  }
  CastNotice {
    ballot_id: ByteArray
  }
  BallotSpoiled {
    ballot_id: ByteArray
  }
  CiphertextTally
  TallyShare {
    guardian_number: Int
  }
  SpoiledShare {
    spoiled_id: ByteArray,
    guardian_number: Int
  }
  PlaintextTally
  SpoiledResult {
    ballot_id: ByteArray
  }
  Summary {
    // verifier_number: Int // TODO nope, could be anyone not just verifiers, so need bytearray
    verifier_id: ByteArray
  }
}

pub fn validate_guardian_number(guardian_number: Int) -> Bool {
  guardian_number > 0 && guardian_number <= max_guardians
}

// TODO test this
pub fn validate_metadata(metadata: PublicRecordMetadata) -> Bool {
  trace @"validate_metadata" : metadata
  when metadata is {

    GuardianPubkey { guardian_number } -> validate_guardian_number(guardian_number)
    TallyShare     { guardian_number } -> validate_guardian_number(guardian_number)
    
    GuardianBackup { guardian_number, backup_order } -> and {
        validate_guardian_number(guardian_number),
        validate_guardian_number(backup_order), // same rules as guardian_number
      }

    GuardianVerification { guardian_number, backup_order } -> and {
        validate_guardian_number(guardian_number),
        validate_guardian_number(backup_order), // same rules as guardian_number
      }

    BallotSubmitted { ballot_id } -> validate_ballot_id(ballot_id)
    CastNotice      { ballot_id } -> validate_ballot_id(ballot_id)
    BallotSpoiled   { ballot_id } -> validate_ballot_id(ballot_id)
    SpoiledResult   { ballot_id } -> validate_ballot_id(ballot_id)

    SpoiledShare { spoiled_id, guardian_number } -> and {
      validate_ballot_id(spoiled_id),
      validate_guardian_number(guardian_number)
    }

    Device  { device_number } -> device_number > 0 &&   device_number <= max_devices

    Summary { .. } -> True // TODO write verify fn

    Manifest        -> True
    JointKey        -> True
    CeremonyDetails -> True
    Constants       -> True
    CiphertextTally -> True
    PlaintextTally  -> True

  }
}

pub type PublicRecord {
  cid: CIDv1,
  metadata: PublicRecordMetadata
}

pub fn validate_record(record: PublicRecord) -> Bool {
  trace @"validate_record"
  validate_metadata(record.metadata) && validate_cid(record.cid)
}

pub fn validate_records(records: List<PublicRecord>) -> Bool {
  trace @"validate_records"
  list.all(records, validate_record)
}
