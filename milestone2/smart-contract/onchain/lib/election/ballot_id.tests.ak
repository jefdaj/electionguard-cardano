use election/ballot_id.{validate_ballot_id}

// Test function
test validate_ballot_id_test() {
  let valid_id = "ballot-9ceb80e2-0797-11f1-b45b-beb24183d45a"
  validate_ballot_id(valid_id) == True
}

test invalid_prefix_test() {
  let invalid_id = "ticket-9ceb80e2-0797-11f1-b45b-beb24183d45a"
  validate_ballot_id(invalid_id) == False
}

test invalid_format_test() {
  let invalid_id = "ballot-invalid-uuid-format"
  validate_ballot_id(invalid_id) == False
}
