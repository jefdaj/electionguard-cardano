// Test that it's simple to burn test tokens from various points in the other tests.

use aiken/fuzz
use aiken/collection/list
use cardano/transaction.{Transaction, Input}
use cardano/assets.{Value}
use election/action as ea
use tests/integration/happy_postpublicrecords as hppr
use tests/mock

// A list of valid STT inputs defined in the "happy path" tests.
const happy_stt_input_list = [
  hppr.admin_input,
  hppr.sub_input,
]

// Return one of the happy_stt_inputs.
pub fn happy_stt_input() -> Fuzzer<Input> {
  fuzz.int_between(0, list.length(happy_stt_input_list) - 1)
    |> fuzz.map(fn(i) {
      when list.at(happy_stt_input_list, i) is {
        Some(input) -> input
        None -> fail @"Index out of bounds"
      }
    })
}

pub fn happy_stt_inputs() -> Fuzzer<List<Input>> { fuzz.set(happy_stt_input()) }

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

// TODO could you write a fuzzer + test prop for this? should always be able to burn

pub fn test_can_burn_hppr_admin_input() {
  can_burn_test_tokens([hppr.admin_input])
}

pub fn test_can_burn_hppr_sub_input() {
  can_burn_test_tokens([hppr.sub_input])
}
