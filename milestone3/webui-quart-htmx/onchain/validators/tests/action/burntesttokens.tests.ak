// Test that tokens defined in the other tests can be burned if needed.

use tests/action/burntesttokens as btt

test prop_can_burn_happy_stt(input via btt.happy_stt_input()) {
  btt.can_burn_test_tokens([input])
}

test prop_can_burn_happy_stts(inputs via btt.happy_stt_inputs()) {
  btt.can_burn_test_tokens(inputs)
}
