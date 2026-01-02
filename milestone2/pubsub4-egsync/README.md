pubsub4: election via IPFS + JSON channels
==========================================

This is an elaboration on [pubsub1-ipfs](../pubsub1-ipfs) that will minimize
the shared public state, replacing it with just a set of JSONL files that
mock pubsub channel smart contracts. Each ElectionGuard role will be paired
with an IPFS node and will keep its own view of the global state based on
messages posted to the "onchain" channels.

tests
-----

Most of the tests still pass. I've disabled the attack tests though, because they need rethinking for the mockchain JSON format.
They may not really be needed at this point anyway?

```
============================= test session starts ==============================
platform linux -- Python 3.12.11, pytest-8.3.5, pluggy-1.5.0 -- /nix/store/1xpm6b51gg6g89w7iba1ys5pcgrg3r7f-python3-3.12.11-env/bin/python3.12
cachedir: .pytest_cache
hypothesis profile 'default' -> database=DirectoryBasedExampleDatabase(PosixPath('/home/jefdaj/myrepos/electionguard-cardano/milestone2/pubsub4-egsync/.hypothesis/examples'))
rootdir: /home/jefdaj/myrepos/electionguard-cardano/milestone2/pubsub4-egsync
plugins: hypothesis-6.130.12
collecting ... collected 51 items

election.py::test_json_voteconfig <- config.py PASSED                    [  1%]
election.py::test_json_contestconfig <- config.py PASSED                 [  3%]
election.py::test_json_electionconfig <- config.py PASSED                [  5%]
election.py::test_json_attackcfg <- config.py PASSED                     [  7%]
election.py::test_json_honestrun <- config.py PASSED                     [  9%]
election.py::test_json_attackrun <- config.py PASSED                     [ 11%]
election.py::test_honest_always_verified PASSED                          [ 13%]
election.py::test_honest_all_verifiers_agree_exactly PASSED              [ 15%]
election.py::test_honest_n_verifications_matches_cfg PASSED              [ 17%]
election.py::test_honest_cast_votes_match_config PASSED                  [ 19%]
election.py::test_honest_spoiled_votes_match_config PASSED               [ 21%]
election.py::test_honest_manifest_verified PASSED                        [ 23%]
election.py::test_honest_ceremony_details_verified PASSED                [ 25%]
election.py::test_honest_gather_announce_verified PASSED                 [ 27%]
election.py::test_honest_all_guardian_backups_verified PASSED            [ 29%]
election.py::test_honest_all_guardian_verifications_verified PASSED      [ 31%]
election.py::test_honest_gather_ceremony_verified PASSED                 [ 33%]
election.py::test_honest_joint_key_verified PASSED                       [ 35%]
election.py::test_honest_build_election_verified PASSED                  [ 37%]
election.py::test_honest_constants_verified PASSED                       [ 39%]
election.py::test_honest_context_verified PASSED                         [ 41%]
election.py::test_honest_gather_constants_verified PASSED                [ 43%]
election.py::test_honest_all_devices_verified PASSED                     [ 45%]
election.py::test_honest_gather_config_verified PASSED                   [ 47%]
election.py::test_honest_all_ballots_submitted_verified PASSED           [ 49%]
election.py::test_honest_all_ballots_cast_verified PASSED                [ 50%]
election.py::test_honest_all_ballots_spoiled_verified PASSED             [ 52%]
election.py::test_honest_all_spoiled_results_verified PASSED             [ 54%]
election.py::test_honest_n_spoiled_decrypted_verified PASSED             [ 56%]
election.py::test_honest_n_cast_spoiled_submitted_verified PASSED        [ 58%]
election.py::test_honest_set_spoiled_decrypted_verified PASSED           [ 60%]
election.py::test_honest_set_cast_spoiled_submitted_verified PASSED      [ 62%]
election.py::test_honest_ballot_sets_verified PASSED                     [ 64%]
election.py::test_honest_ciphertext_tally_verified PASSED                [ 66%]
election.py::test_honest_tally_aggregation_verified PASSED               [ 68%]
election.py::test_honest_plaintext_tally_verified PASSED                 [ 70%]
election.py::test_honest_tally_decryption_verified PASSED                [ 72%]
election.py::test_honest_gather_tally_verified PASSED                    [ 74%]
election.py::test_honest_gather_decryptions_verified PASSED              [ 76%]
election.py::test_honest_gather_election_verified PASSED                 [ 78%]
election.py::test_attack_admin_withhold_manifest SKIPPED (unconditional
skip)                                                                    [ 80%]
election.py::test_attack_admin_ghost_after_vote SKIPPED (unconditional
skip)                                                                    [ 82%]
election.py::test_attack_device_withhold_submitted_ballot SKIPPED        [ 84%]
election.py::test_attack_device_withhold_cast_ballot SKIPPED             [ 86%]
election.py::test_attack_device_withhold_spoiled_ballot SKIPPED          [ 88%]
election.py::test_attack_device_mutate_submitted_ballot SKIPPED          [ 90%]
election.py::test_attack_device_mutate_spoiled_ballot SKIPPED            [ 92%]
election.py::test_attack_guardian_withhold_tally_share SKIPPED           [ 94%]
election.py::test_attack_guardian_withhold_spoiled_share SKIPPED         [ 96%]
election.py::test_verifiers_notice_attacks SKIPPED (unconditional skip)  [ 98%]
election.py::test_attacks_are_logged SKIPPED (unconditional skip)        [100%]

======================== 40 passed, 11 skipped in 6.25s ========================
```

Shared state
------------

Instead of `data/public`, each ElectionGuard role will have its own separate
set of IPFS files reconstructed from "onchain" JSON messages, like this:

```
data/
├── onchain
│   ├── admin_1.jsonl
│   ├── device_1.jsonl
│   ├── guardian_1.jsonl
│   └── verifier_1.jsonl
└── private
    ├── admin_1
    ├── device_1
    │   ├── egsync
    │   │   ├── 1_config
    │   │   │   ├── 1_announce
    │   │   │   ├── 2_ceremony
    │   │   │   ├── 3_election
    │   │   │   └── 4_devices
    │   │   ├── 2_ballots
    │   │   │   ├── 1_submitted
    │   │   │   ├── 2_cast
    │   │   │   └── 3_spoiled
    │   │   └── 3_results
    │   │       ├── 1_shares
    │   │       ├── 2_combined
    │   │       └── 3_summary.json
    │   └── tmp
    │       ├── logs
    │       │   ├── attack.log
    │       │   └── verify.log
    │       └── plaintext_ballots
    │           ├── ballot-16fa6ff6-e119-11f0-9481-4210f8977e3d.json
    │           ├── ballot-191a24fc-e119-11f0-ac7d-4210f8977e3d.json
    │           └── ballot-1b2c94fa-e119-11f0-92f5-4210f8977e3d.json
    ├── guardian_1
    └── verifier_1
```

Message format
--------------

One of the main points of this exercise is to refine the format.
So far I'm thinking:

- channel is a JSONL opened append-only
- each append corresponds to a UTXO
- generic message types: `open_channel`, `close_channel`, `post_public_records` (a list of public record messages)
- public record message types:

    * match current `to_public_record` calls in Python code
    * except that the file content is replaced with a CID
- maybe also `authorize_channel` for admin to authorize the guardians + devices + official verifiers to post
  (later, should include a public option for anyone to post disputes and verifications)
- and `add_relay` + `remove_relay` for the admin to optionally say where they'll be serving the IPFS files from
  (either a self hosted ipfs-cluster or pinning service, probably)

egsync
------

Maybe it's time to start the egsync container(s) and have the ElectionGuard ones communicate with them via an API?
It can be a subscriber all the time and also publish things when requested to.
It could have a very simple API for now:

- post `to_public_record`
- get `from_public_record`

The mapping of those calls <--> filenames can be moved from utils to the new egsync.
