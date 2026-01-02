MockChain + Local IPFS
======================

This is an elaboration on [pubsub1-ipfs](../pubsub1-ipfs) that minimizes
the shared public state, replacing it with just a set of JSONL files that
mock pubsub channel smart contracts. Each ElectionGuard container is paired
with an IPFS node and will keep its own view of the global state based on
messages posted to the "mockchain" channels.

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

Next steps
----------

- add `add_relay` + `remove_relay` for the admin to optionally say where they'll be serving the IPFS files from
  (either a self hosted ipfs-cluster or pinning service, probably)

- add an election status endpoint to egsync that says which phase is currently
  going, and therefore which actions are valid

- start making the containers less dependent on a top level orchestration
  script by having them check the status endpoint and continue their own protocols
