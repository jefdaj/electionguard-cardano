use aiken/builtin
use aiken/primitive/bytearray

// This is probably excessive for an initial mainnet demo,
// but helped me get used to Aiken. Can always remove some of it...

/// Expected format: "ballot-" followed by a UUID v1 (8-4-4-4-12 hex digits)
pub fn validate_ballot_id(id: ByteArray) -> Bool {
  trace @"validate_ballot_id"

  // Check if starts with "ballot-"
  let prefix = bytearray.slice(id, 0, 6)
  let has_valid_prefix = prefix == builtin.encode_utf8(@"ballot-")

  // Check if the rest matches UUID format
  when has_valid_prefix is {
    True -> {
      let uuid_part = bytearray.slice(id, 7, 43)
      validate_uuid_format(uuid_part)
    }
    False -> False
  }

}

/// Validates UUID format: 8-4-4-4-12 hex characters with hyphens
pub fn validate_uuid_format(uuid: ByteArray) -> Bool {
  trace @"validate_uuid_format"

  let is_correct_length = bytearray.length(uuid) == 36

  // Check hyphens are in correct positions (indices 8, 13, 18, 23)
  // ASCII code for '-' is 45
  let hyphen_8  = bytearray.at(uuid,  8) == 45
  let hyphen_13 = bytearray.at(uuid, 13) == 45
  let hyphen_18 = bytearray.at(uuid, 18) == 45
  let hyphen_23 = bytearray.at(uuid, 23) == 45
  let hyphens_valid = hyphen_8 && hyphen_13 && hyphen_18 && hyphen_23

  when is_correct_length && hyphens_valid is {
    True -> {
      // Validate hex characters in each segment
      is_hex_segment(uuid, 0, 8) &&    // 8 chars
      is_hex_segment(uuid, 9, 13) &&   // 4 chars
      is_hex_segment(uuid, 14, 18) &&  // 4 chars
      is_hex_segment(uuid, 19, 23) &&  // 4 chars
      is_hex_segment(uuid, 24, 36)     // 12 chars
    }
    False -> False
  }

}

/// Checks if all characters in a byte range are valid hexadecimal
pub fn is_hex_segment(bytes: ByteArray, start: Int, end: Int) -> Bool {
  trace @"is_hex_segment"
  when start < end is {
    True -> {
      let byte = bytearray.at(bytes, start)
      let is_hex =
        (byte >= 48 && byte <= 57) ||   // 0-9
        (byte >= 97 && byte <= 102) ||  // a-f
        (byte >= 65 && byte <= 70)      // A-F (TODO remove?)

      when is_hex is {
        True -> is_hex_segment(bytes, start + 1, end)
        False -> False
      }
    }
    False -> True
  }
}
