use election/types/ballot_id

test valid_hex_segment_test() {
  // hex up until the last byte (9)
  let test_bytes = "9ceb80e2-"
  ballot_id.is_hex_segment(test_bytes, 0, 8) == True
}

test invalid_hex_segment_test() {
  // hex up until the last byte (9)
  let test_bytes = "9ceb80e2-"
  ballot_id.is_hex_segment(test_bytes, 0, 9) == False
}

test valid_uuid_test() {
  let valid_uuid = "9ceb80e2-0797-11f1-b45b-beb24183d45a"
  ballot_id.validate_uuid_format(valid_uuid) == True
}

test valid_ballot_id_test() {
  let valid_id = "ballot-9ceb80e2-0797-11f1-b45b-beb24183d45a"
  ballot_id.validate_ballot_id(valid_id) == True
}

test invalid_prefix_test() {
  let invalid_id = "ticket-9ceb80e2-0797-11f1-b45b-beb24183d45a"
  ballot_id.validate_ballot_id(invalid_id) == False
}

test invalid_format_test() {
  let invalid_id = "ballot-invalid-uuid-format"
  ballot_id.validate_ballot_id(invalid_id) == False
}
