Test Script
===========

This script will generate arbitrary election configs, run the corresponding
test elections, and verify some properties of the output files. The elections
can be slow, but it caches the output files so at least editing and re-running
the property tests is fast.

```bash
# generate 10 arbitrary configs,
# run the corresponding elections,
# and verify properties of the output files
# explicit random seed is optional
# sudo is required to work around docker bind mount permission errors

$ nix develop
$ sudo TEST_RANDOM_SEED=1234 ./test.py

/nix/store/jjfqmy1a6svyhs2x4ymnxl0b1zmdpzmm-python3-3.12.8-env/lib/python3.12/site-packages/hypothesis/strategies/_internal/core.py:1838: HypothesisDeprecationWarning: There is no reason to use @st.composite on a function which does not call the provided draw() function internally.
  note_deprecation(
========================= test session starts =========================
platform linux -- Python 3.12.8, pytest-8.3.3, pluggy-1.5.0 -- /nix/store/jjfqmy1a6svyhs2x4ymnxl0b1zmdpzmm-python3-3.12.8-env/bin/python3.12
cachedir: .pytest_cache
hypothesis profile 'default' -> database=DirectoryBasedExampleDatabase(PosixPath('/home/jefdaj/myrepos/electionguard-cardano/milestone1/tests/.hypothesis/examples'))
rootdir: /home/jefdaj/myrepos/electionguard-cardano/milestone1/tests
plugins: hypothesis-6.112.2
collected 40 items                                                                                                      

test.py::test_roundtrip_arionconfig PASSED                      [  2%]
test.py::test_roundtrip_voteconfig PASSED                       [  5%]
test.py::test_roundtrip_contestconfig PASSED                    [  7%]
test.py::test_roundtrip_electionconfig PASSED                   [ 10%]
test.py::test_roundtrip_projectconfig PASSED                    [ 12%]
test.py::test_election_finished PASSED                          [ 15%]
test.py::test_all_election_verifiers_agree_exactly PASSED       [ 17%]
test.py::test_n_verifications_matches_cfg PASSED                [ 20%]
test.py::test_cast_votes_match_config PASSED                    [ 22%]
test.py::test_spoiled_votes_match_config PASSED                 [ 25%]
test.py::test_manifest_verified PASSED                          [ 27%]
test.py::test_ceremony_details_verified PASSED                  [ 30%]
test.py::test_gather_announce_verified PASSED                   [ 32%]
test.py::test_all_guardian_backups_verified PASSED              [ 35%]
test.py::test_all_guardian_verifications_verified PASSED        [ 37%]
test.py::test_gather_ceremony_verified PASSED                   [ 40%]
test.py::test_joint_key_verified PASSED                         [ 42%]
test.py::test_build_election_verified PASSED                    [ 45%]
test.py::test_constants_verified PASSED                         [ 47%]
test.py::test_internal_manifest_verified PASSED                 [ 50%]
test.py::test_context_verified PASSED                           [ 52%]
test.py::test_gather_constants_verified PASSED                  [ 55%]
test.py::test_all_devices_verified PASSED                       [ 57%]
test.py::test_gather_config_verified PASSED                     [ 60%]
test.py::test_all_ballots_submitted_verified PASSED             [ 62%]
test.py::test_all_ballots_cast_verified PASSED                  [ 65%]
test.py::test_all_ballots_spoiled_verified PASSED               [ 67%]
test.py::test_all_spoiled_results_verified PASSED               [ 70%]
test.py::test_n_spoiled_decrypted_verified PASSED               [ 72%]
test.py::test_n_cast_spoiled_submitted_verified PASSED          [ 75%]
test.py::test_set_spoiled_decrypted_verified PASSED             [ 77%]
test.py::test_set_cast_spoiled_submitted_verified PASSED        [ 80%]
test.py::test_ballot_sets_verified PASSED                       [ 82%]
test.py::test_ciphertext_tally_verified PASSED                  [ 85%]
test.py::test_tally_aggregation_verified PASSED                 [ 87%]
test.py::test_plaintext_tally_verified PASSED                   [ 90%]
test.py::test_tally_decryption_verified PASSED                  [ 92%]
test.py::test_gather_tally_verified PASSED                      [ 95%]
test.py::test_gather_decryptions_verified PASSED                [ 97%]
test.py::test_gather_election_verified PASSED                   [100%]

========================== warnings summary ===========================
../../../../../../nix/store/jjfqmy1a6svyhs2x4ymnxl0b1zmdpzmm-python3-3.12.8-env/lib/python3.12/site-packages/hypothesis/strategies/_internal/core.py:1838
  /nix/store/jjfqmy1a6svyhs2x4ymnxl0b1zmdpzmm-python3-3.12.8-env/lib/python3.12/site-packages/hypothesis/strategies/_internal/core.py:1838: HypothesisDeprecationWarning: There is no reason to use @st.composite on a function which does not call the provided draw() function internally.
    note_deprecation(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
============== 40 passed, 1 warning in 294.21s (0:04:54) ==============

$ tree -L 2 tests
tests
├── test2ac2d
│   ├── data
│   ├── election.json
│   └── election.log
├── test4dceb
│   ├── data
│   ├── election.json
│   └── election.log
├── ...
└── testb2523
    ├── data
    ├── election.json
    └── election.log

21 directories, 20 files
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

## TODO

- [x] Re-learn some Hypothesis basics
- [x] Have `verifier.py` send output to a log rather than printing if `--output` given
- [x] Set up the "generate config, run election, assert about results" loop
- [x] Rearrange `election.json`: "election" -> "roles", "votes" -> "contests", question inside contests
- [x] Have `verifier.py` save a nested dict of all passing verifications in its json file
- [ ] Move `test.py` code -> `election.py`? or `conftest.py`?
