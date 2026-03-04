use aiken/crypto.{VerificationKeyHash}
use cardano/transaction.{InlineDatum, Output}

use election/record.{PublicRecord}

pub type ChannelState {

  // All transactions must be signed by the admin's key.
  // TODO allow the channel to be created by a separate admin
  publisher: VerificationKeyHash,

  // TODO subchannels

  // Just the latest batch of records; have to index the STT asset history to get the full list.
  // Should be set to [] when doing any non-publish transaction.
  new_records: List<PublicRecord>,

  // For detecting rollbacks or errors
  seq: Int
}

pub fn publisher_unchanged(
  old_publisher: VerificationKeyHash,
  stt_output: Output
) -> Bool {
  expect InlineDatum(new_datum) = stt_output.datum
  expect new_config: ChannelState = new_datum
  new_config.publisher == old_publisher
}

pub fn sequence_incremented(
  old_seq: Int,
  stt_output: Output
) -> Bool {
  expect InlineDatum(new_datum) = stt_output.datum
  expect new_config: ChannelState = new_datum
  new_config.seq == (old_seq + 1)
}
