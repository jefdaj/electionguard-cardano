use aiken/collection/list

use election/cid.{CIDv1, validate_cid}

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
    verifier_number: Int
  }
}

// TODO does this conflict with any built-in type name?
pub type PublicRecord {
  cid: CIDv1,
  metadata: PublicRecordMetadata
}

pub fn validate_record(record: PublicRecord) -> Bool {
  validate_cid(record.cid)
  // TODO validate metadata
}

/// Validate a list of records
pub fn validate_records(records: List<PublicRecord>) -> Bool {
  trace @"validate_records"
  list.all(records, validate_record)
}
