use aiken/builtin
use aiken/primitive/bytearray
use aiken/primitive/string

pub type ChannelId = ByteArray

// TODO rename from_string?
// TODO avoid using this except in test modules? shouldn't be needed on chain
pub fn channel_id(channel_name: String) -> ChannelId {
  trace @"channel_id"
  string.to_bytearray(channel_name)
}

/// Validate channel identifier format.
/// Valid identifiers:
/// - "admin"
/// - "guardian", "device", or "verifier" + number 1-100
pub fn validate_channel_id(channel_id: ChannelId) -> Bool {
  trace @"validate_channel_id"
  if channel_id == "admin" {
    True
  } else {
    // Check for guardian/device/verifier prefix
    let has_guardian = bytearray.starts_with(channel_id, "guardian")
    let has_device   = bytearray.starts_with(channel_id, "device")
    let has_verifier = bytearray.starts_with(channel_id, "verifier")
    if !(has_guardian || has_device || has_verifier) {
      False
    } else {
      // Extract the number part
      let prefix_len = if has_device { 6 } else { 8 } // length of word part
      let total_len = builtin.length_of_bytearray(channel_id)
      let number_part = builtin.slice_bytearray(prefix_len, total_len, channel_id)
      let num_len = builtin.length_of_bytearray(number_part)
      if num_len < 1 || num_len > 3 {
        False
      } else {
        when parse_int(number_part) is {
          Some(n) -> n >= 1 && n <= 100 && !has_leading_zero(number_part)
          None -> False
        }
      }

    }
  }
}

/// Helper to check for leading zeros (rejects "01", "001", etc.)
fn has_leading_zero(bytes: ByteArray) -> Bool {
  let first_char = builtin.index_bytearray(bytes, 0)
  first_char == 48 && builtin.length_of_bytearray(bytes) > 1  // '0' is ASCII 48
}

/// Parse ByteArray to int (digits only)
fn parse_int(bytes: ByteArray) -> Option<Int> {
  do_parse_int(bytes, 0, 0)
}

fn do_parse_int(bytes: ByteArray, index: Int, acc: Int) -> Option<Int> {
  let len = builtin.length_of_bytearray(bytes)
  if index >= len {
    Some(acc)
  } else {
    let byte = builtin.index_bytearray(bytes, index)
    // ASCII '0' = 48, '9' = 57
    if byte >= 48 && byte <= 57 {
      let digit = byte - 48
      do_parse_int(bytes, index + 1, acc * 10 + digit)
    } else {
      None
    }
  }
}
