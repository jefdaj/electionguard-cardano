// Test that it's simple to burn test tokens from various points in the other tests.

use aiken/fuzz
use aiken/collection/list
use cardano/transaction.{Transaction, Input}
use cardano/assets.{Value}
use election/action as ea
use tests/integration/happy_subchannel
use tests/integration/happy_election
use tests/integration/happy_postpublicrecords
use tests/mock

const happy_stt_inputs_plain = [
  happy_election.admin_tx2_in0,
  happy_election.admin_tx3_in0,
  happy_election.device1_tx1_in0,
  happy_election.guardian1_tx1_in0,
  happy_election.guardian2_tx1_in0,
  happy_election.guardian3_tx1_in0,
  happy_election.verifier1_tx1_in0,
  happy_postpublicrecords.admin_input,
  happy_postpublicrecords.sub_input,
  happy_subchannel.admin_pre_add_input,
  happy_subchannel.admin_pre_rm_input,
  happy_subchannel.sub_post_add_input,
]

const happy_stt_inputs_from_lists = list.flat_map(
  [
    happy_subchannel.sub_pre_rm_inputs_multi(),
  ],
  fn(a) { a }
)

const happy_stt_inputs_from_triples = list.map(
  [
    happy_election.admin_tx1_triple(),
    happy_election.admin_tx3_triple(),
    happy_election.admin_tx4_triple(),
    happy_election.admin_tx5_triple(),
    happy_election.admin_tx6_triple(),
    happy_election.admin_tx7_triple(),
    happy_election.device1_tx1_triple(),
    happy_election.device1_tx2_triple(),
    happy_election.device1_tx3_triple(),
    happy_election.guardian1_tx1_triple(),
    happy_election.guardian1_tx2_triple(),
    happy_election.guardian1_tx3_triple(),
    happy_election.guardian1_tx4_triple(),
    happy_election.guardian1_tx5_triple(),
    happy_election.guardian2_tx1_triple(),
    happy_election.guardian2_tx2_triple(),
    happy_election.guardian2_tx3_triple(),
    happy_election.guardian2_tx4_triple(),
    happy_election.guardian2_tx5_triple(),
    happy_election.guardian3_tx1_triple(),
    happy_election.guardian3_tx2_triple(),
    happy_election.guardian3_tx3_triple(),
    happy_election.guardian3_tx4_triple(),
    happy_election.guardian3_tx5_triple(),
    happy_election.verifier1_tx1_triple()
  ],
  fn(triple) {
    let (_, _, input) = triple
    input
  }
)

// A list of valid STT inputs defined in the "happy path" tests.
const happy_stt_input_list = list.flat_map(
  [
    happy_stt_inputs_plain,
    happy_stt_inputs_from_lists,
    happy_stt_inputs_from_triples,
  ],
  fn(a) { a }
)

// Return one of the happy_stt_inputs.
pub fn happy_stt_input() -> Fuzzer<Input> {
  fuzz.int_between(0, list.length(happy_stt_input_list) - 1)
    |> fuzz.map(fn(i) {
      trace @"i" : i
      when list.at(happy_stt_input_list, i) is {
        Some(input) -> input
        None -> fail @"Index out of bounds"
      }
    })
}

// TODO is it a problem that lots of inputs are duplicated here?
pub fn happy_stt_inputs() -> Fuzzer<List<Input>> { fuzz.list(happy_stt_input()) }

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
