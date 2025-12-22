Test Script
===========

This script will generate arbitrary election configs, run the corresponding
test elections, and verify some properties of the output files. The elections
can be slow, but it caches the output files so at least editing and re-running
the property tests is fast.

```bash
$ nix develop
$ ./test.sh

============================= test session starts ==============================
platform linux -- Python 3.12.8, pytest-8.3.3, pluggy-1.5.0 -- /nix/store/jjfqmy1a6svyhs2x4ymnxl0b1zmdpzmm-python3-3.12.8-env/bin/python3.12
cachedir: .pytest_cache
hypothesis profile 'default' -> database=DirectoryBasedExampleDatabase(PosixPath('/home/jefdaj/myrepos/electionguard-cardano/milestone1/tests/.hypothesis/examples'))
rootdir: /home/jefdaj/myrepos/electionguard-cardano/milestone1/tests
plugins: hypothesis-6.112.2
collecting ... collected 52 items

election.py::test_json_arionconfig <- config.py PASSED                   [  1%]
election.py::test_json_voteconfig <- config.py PASSED                    [  3%]
election.py::test_json_contestconfig <- config.py PASSED                 [  5%]
election.py::test_json_electionconfig <- config.py PASSED                [  7%]
election.py::test_json_attackcfg <- config.py PASSED                     [  9%]
election.py::test_json_honestrun <- config.py PASSED                     [ 11%]
election.py::test_json_attackrun <- config.py PASSED                     [ 13%]
election.py::test_honest_always_verified PASSED                          [ 15%]
election.py::test_honest_all_verifiers_agree_exactly PASSED              [ 17%]
election.py::test_honest_n_verifications_matches_cfg PASSED              [ 19%]
election.py::test_honest_cast_votes_match_config PASSED                  [ 21%]
election.py::test_honest_spoiled_votes_match_config PASSED               [ 23%]
election.py::test_honest_manifest_verified PASSED                        [ 25%]
election.py::test_honest_ceremony_details_verified PASSED                [ 26%]
election.py::test_honest_gather_announce_verified PASSED                 [ 28%]
election.py::test_honest_all_guardian_backups_verified PASSED            [ 30%]
election.py::test_honest_all_guardian_verifications_verified PASSED      [ 32%]
election.py::test_honest_gather_ceremony_verified PASSED                 [ 34%]
election.py::test_honest_joint_key_verified PASSED                       [ 36%]
election.py::test_honest_build_election_verified PASSED                  [ 38%]
election.py::test_honest_constants_verified PASSED                       [ 40%]
election.py::test_honest_internal_manifest_verified PASSED               [ 42%]
election.py::test_honest_context_verified PASSED                         [ 44%]
election.py::test_honest_gather_constants_verified PASSED                [ 46%]
election.py::test_honest_all_devices_verified PASSED                     [ 48%]
election.py::test_honest_gather_config_verified PASSED                   [ 50%]
election.py::test_honest_all_ballots_submitted_verified PASSED           [ 51%]
election.py::test_honest_all_ballots_cast_verified PASSED                [ 53%]
election.py::test_honest_all_ballots_spoiled_verified PASSED             [ 55%]
election.py::test_honest_all_spoiled_results_verified PASSED             [ 57%]
election.py::test_honest_n_spoiled_decrypted_verified PASSED             [ 59%]
election.py::test_honest_n_cast_spoiled_submitted_verified PASSED        [ 61%]
election.py::test_honest_set_spoiled_decrypted_verified PASSED           [ 63%]
election.py::test_honest_set_cast_spoiled_submitted_verified PASSED      [ 65%]
election.py::test_honest_ballot_sets_verified PASSED                     [ 67%]
election.py::test_honest_ciphertext_tally_verified PASSED                [ 69%]
election.py::test_honest_tally_aggregation_verified PASSED               [ 71%]
election.py::test_honest_plaintext_tally_verified PASSED                 [ 73%]
election.py::test_honest_tally_decryption_verified PASSED                [ 75%]
election.py::test_honest_gather_tally_verified PASSED                    [ 76%]
election.py::test_honest_gather_decryptions_verified PASSED              [ 78%]
election.py::test_honest_gather_election_verified PASSED                 [ 80%]
election.py::test_attack_admin_withhold_manifest PASSED                  [ 82%]
election.py::test_attack_admin_ghost_after_vote PASSED                   [ 84%]
election.py::test_attack_device_withhold_submitted_ballot PASSED         [ 86%]
election.py::test_attack_device_withhold_cast_ballot PASSED              [ 88%]
election.py::test_attack_device_withhold_spoiled_ballot PASSED           [ 90%]
election.py::test_attack_device_mutate_submitted_ballot PASSED           [ 92%]
election.py::test_attack_guardian_withhold_tally_share PASSED            [ 94%]
election.py::test_attack_guardian_withhold_spoiled_share PASSED          [ 96%]
election.py::test_verifiers_notice_attacks PASSED                        [ 98%]
election.py::test_attacks_are_logged PASSED                              [100%]

=============================== warnings summary ===============================
../../../../../../nix/store/jjfqmy1a6svyhs2x4ymnxl0b1zmdpzmm-python3-3.12.8-env/lib/python3.12/site-packages/hypothesis/strategies/_internal/core.py:1838
  /nix/store/jjfqmy1a6svyhs2x4ymnxl0b1zmdpzmm-python3-3.12.8-env/lib/python3.12/site-packages/hypothesis/strategies/_internal/core.py:1838: HypothesisDeprecationWarning: There is no reason to use @st.composite on a function which does not call the provided draw() function internally.
    note_deprecation(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
================== 52 passed, 1 warning in 2430.53s (0:40:30) ==================

$ tree -L 2 tests
tests
├── test01576
│   ├── data
│   ├── election.json
│   └── election.log
├── test0500d
│   ├── data
│   ├── election.json
│   └── election.log
├── ...
└── testff797
    ├── data
    ├── election.json
    └── election.log

193 directories, 192 files
```

### Single election for debugging

You can still use `election.py` as before in ../election,
including with the `--single-step` option.

```bash
$ nix develop
$ ./election.py --logfile test.log --project-config election.json
$ tree -L 2 data/
data/
├── private
│   ├── admin_1
│   ├── device_1
│   ├── device_2
│   ├── device_3
│   ├── device_4
│   ├── guardian_1
│   ├── guardian_2
│   ├── guardian_3
│   ├── verifier_1
│   └── verifier_2
└── public
    ├── 1_config
    ├── 2_ballots
    ├── 3_results
    └── 4_verify

17 directories, 0 files
```

## Out of scope for now

There are some parts of the election that aren't checked in the current implementation,
but seem important to me. They should be addressed before doing a production version:

- admin can alter election constants without anyone noticing
- device can alter spoiled ballot nonces (presumably a voter's personal verifier would catch this!)
