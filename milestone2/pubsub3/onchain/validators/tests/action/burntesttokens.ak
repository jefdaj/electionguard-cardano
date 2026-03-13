// Test that it's simple to burn test tokens from various points in the other tests.

use aiken/collection/list
use cardano/transaction.{Transaction, Input}
use cardano/assets.{Value}
use election/action as ea
use tests/integration/happy_postpublicrecords as hppr
use tests/mock

fn make_burn_value(inputs: List<Input>) -> Value {
  list.foldl(
    inputs,
    assets.zero,
    fn(input, acc) {
      assets.merge(acc, assets.negate(input.output.value))
    },
  )
}

// TODO should this require a policy_id?
pub fn can_burn_test_tokens(inputs: List<Input>) -> Bool {
  let burn_val = make_burn_value(inputs)
  let tx = Transaction {
    ..transaction.placeholder,
    inputs: inputs,
    mint: burn_val,
  }
  mock.election_validate(tx, ea.BurnTestTokens)
}

// TODO test_burn_sub_output0

pub fn test_can_burn_hppr_admin_input() {
  can_burn_test_tokens([hppr.admin_input])
}

pub fn test_can_burn_hppr_sub_input() {
  can_burn_test_tokens([hppr.sub_input])
}

// TODO then run them in the other module of course
