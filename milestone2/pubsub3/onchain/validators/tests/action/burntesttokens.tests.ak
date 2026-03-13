// Test that it's simple to burn test tokens from various points in the other tests.

use tests/action/burntesttokens as btt

test can_burn_hppr_admin_input() {
  btt.test_can_burn_hppr_admin_input()
}

test can_burn_hppr_sub_input() {
  btt.test_can_burn_hppr_sub_input()
}

test prop_can_burn_happy_stt(input via btt.happy_stt_input()) {
  btt.can_burn_test_tokens([input])
}

test prop_can_burn_happy_stts(inputs via btt.happy_stt_inputs()) {
  btt.can_burn_test_tokens(inputs)
}
