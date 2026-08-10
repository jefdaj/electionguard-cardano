use aiken/primitive/bytearray
use aiken/collection/list

use election/types/ipfs_cid.{IpfsCid, validate_ipfs_cid}
use election/types/ballot_id.{validate_ballot_id}

// These aren't part of the ElectionGuard protocol as far as I know,
// but it seems reasonable to err on the side of safety for now.
// I've run elections with up to 99 guardians in the Python code.
// TODO will we hit any Cardano TX size limits before that?
const max_guardians: Int = 100
const max_devices  : Int = 100
// const max_verifiers: Int = 100

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
  Context
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
  // trace @"validate_guardian_number"
  guardian_number > 0 && guardian_number <= max_guardians
}

/// Validates that a ByteArray represents a verifier ID with the following rules:
/// - Must be under 20 characters when decoded
/// - Must match pattern: [a-z]* followed by an optional number (max 3 digits)
/// They could all be relaxed if needed.
// TODO rename validate_channel_id and put with ChannelId definition?
pub fn validate_verifier_id(id: ByteArray) -> Bool {
  trace @"validate_verifier_id"
  let length = bytearray.length(id)
  if length >= 20 {
    False
  } else {
    validate_verifier_id_pattern(id, 0, length, True, 0)
  }
}

/// Recursive helper to validate the pattern
/// - in_letters: True if we're still in the letter portion
/// - digit_count: Number of digits encountered
fn validate_verifier_id_pattern(
  id: ByteArray,
  index: Int,
  length: Int,
  in_letters: Bool,
  digit_count: Int,
) -> Bool {
  if index >= length {
    // Reached end successfully
    True
  } else {
    let byte = bytearray.at(id, index)

    // Check if it's a lowercase letter (a-z: 97-122)
    if byte >= 97 && byte <= 122 {
      if in_letters {
        // Still in letter portion
        validate_verifier_id_pattern(id, index + 1, length, True, digit_count)
      } else {
        // Found a letter after digits - invalid
        False
      }
    // Check if it's a digit (0-9: 48-57)
    } else if byte >= 48 && byte <= 57 {
      if digit_count < 3 {
        // Transition to digit portion, increment count
        validate_verifier_id_pattern(id, index + 1, length, False, digit_count + 1)
      } else {
        // More than 3 digits - invalid
        False
      }
    } else {
      // Any other character is invalid
      False
    }
  }
}

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

    Summary { verifier_id } -> validate_verifier_id(verifier_id)

    Manifest        -> True
    JointKey        -> True
    Context         -> True
    CeremonyDetails -> True
    Constants       -> True
    CiphertextTally -> True
    PlaintextTally  -> True

  }
}

pub type PublicRecord {
  ipfs_cid: IpfsCid,
  metadata: PublicRecordMetadata
}

pub fn validate_record(record: PublicRecord) -> Bool {
  // trace @"validate_record"
  validate_metadata(record.metadata) && validate_ipfs_cid(record.ipfs_cid)
}

pub fn validate_records(records: List<PublicRecord>) -> Bool {
  // trace @"validate_records"
  list.all(records, validate_record)
}
