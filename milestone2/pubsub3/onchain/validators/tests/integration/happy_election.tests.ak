// Happy path through a full election, posting statically generated CIDs.
// This one has enough going on that I need variable naming conventions:
//
// 1. first channel name: admin, guardian1, ...
// 2. then tx<N> where N == seq: 0, 1, ...
// 3. type: state, input, output, ...
// 4. finally an input/output index if needed: 0, 1, ...
//
// Examples: admin_tx0_state, device1_tx3_input, device1_tx3_output0

// use aiken/primitive/string
// use election/record as er
// use tests/data/static_election_records as sr
// use tests/mock

// =================================
// initial solo admin section:
// 1. init election
// 2. announce config
// 3. onboarding (add subchannels)
// =================================

// =================================
// parallel admin section:
// 1. ceremony
// 2. finalize config (device here?)
// 3. voting
// 4. results tally
// 5. results decrypt
// 6. verify
// =================================

// =================================
// parallel subchannels sections
// (grouped by channel):
// 1. key ceremony
// 2. device announce?
// 3. voting
// 4. results decrypt
// 5. verify
// =================================

// =================================
// final solo admin section:
// 1. rm subchannels
// 2. end election
// =================================
