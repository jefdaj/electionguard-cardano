Test Script
===========

This script will generate arbitrary election configs, run the corresponding
test elections, and verify some properties of the output files. The elections
can be slow, but it caches the output files so at least editing and re-running
the property tests is fast.

```bash
$ nix develop

# explicit random seed is optional
# sudo is required to work around docker bind mount permission errors
$ sudo TEST_RANDOM_SEED=1234 ./test.py

=========================== test session starts ===========================
platform linux -- Python 3.12.8, pytest-8.3.3, pluggy-1.5.0 -- /nix/store/jjfqmy1a6svyhs2x4ymnxl0b1zmdpzmm-python3-3.12.8-env/bin/python3.12
cachedir: .pytest_cache
hypothesis profile 'default' -> database=DirectoryBasedExampleDatabase(PosixPath('/home/jefdaj/myrepos/electionguard-cardano/milestone1/tests/.hypothesis/examples'))
rootdir: /home/jefdaj/myrepos/electionguard-cardano/milestone1/tests
plugins: hypothesis-6.112.2
collected 44 items

election.py::test_roundtrip_arionconfig <- config.py PASSED          [  2%]
election.py::test_roundtrip_voteconfig <- config.py PASSED           [  4%]
election.py::test_roundtrip_contestconfig <- config.py PASSED        [  6%]
election.py::test_roundtrip_electionconfig <- config.py PASSED       [  9%]
election.py::test_roundtrip_attackcfg <- config.py PASSED            [ 11%]
election.py::test_roundtrip_honestrun <- config.py PASSED            [ 13%]
election.py::test_roundtrip_attackrun <- config.py PASSED            [ 15%]
election.py::test_honest_election_finishes PASSED                    [ 18%]
election.py::test_all_election_verifiers_agree_exactly PASSED        [ 20%]
election.py::test_n_verifications_matches_cfg PASSED                 [ 22%]
election.py::test_cast_votes_match_config PASSED                     [ 25%]
election.py::test_spoiled_votes_match_config PASSED                  [ 27%]
election.py::test_manifest_verified PASSED                           [ 29%]
election.py::test_ceremony_details_verified PASSED                   [ 31%]
election.py::test_gather_announce_verified PASSED                    [ 34%]
election.py::test_all_guardian_backups_verified PASSED               [ 36%]
election.py::test_all_guardian_verifications_verified PASSED         [ 38%]
election.py::test_gather_ceremony_verified PASSED                    [ 40%]
election.py::test_joint_key_verified PASSED                          [ 43%]
election.py::test_build_election_verified PASSED                     [ 45%]
election.py::test_constants_verified PASSED                          [ 47%]
election.py::test_internal_manifest_verified PASSED                  [ 50%]
election.py::test_context_verified PASSED                            [ 52%]
election.py::test_gather_constants_verified PASSED                   [ 54%]
election.py::test_all_devices_verified PASSED                        [ 56%]
election.py::test_gather_config_verified PASSED                      [ 59%]
election.py::test_all_ballots_submitted_verified PASSED              [ 61%]
election.py::test_all_ballots_cast_verified PASSED                   [ 63%]
election.py::test_all_ballots_spoiled_verified PASSED                [ 65%]
election.py::test_all_spoiled_results_verified PASSED                [ 68%]
election.py::test_n_spoiled_decrypted_verified PASSED                [ 70%]
election.py::test_n_cast_spoiled_submitted_verified PASSED           [ 72%]
election.py::test_set_spoiled_decrypted_verified PASSED              [ 75%]
election.py::test_set_cast_spoiled_submitted_verified PASSED         [ 77%]
election.py::test_ballot_sets_verified PASSED                        [ 79%]
election.py::test_ciphertext_tally_verified PASSED                   [ 81%]
election.py::test_tally_aggregation_verified PASSED                  [ 84%]
election.py::test_plaintext_tally_verified PASSED                    [ 86%]
election.py::test_tally_decryption_verified PASSED                   [ 88%]
election.py::test_gather_tally_verified PASSED                       [ 90%]
election.py::test_gather_decryptions_verified PASSED                 [ 93%]
election.py::test_gather_election_verified PASSED                    [ 95%]
election.py::test_verifiers_notice_attacks PASSED                    [ 97%]
election.py::test_attacks_are_logged PASSED                          [100%]

============================= warnings summary =============================
../../../../../../nix/store/jjfqmy1a6svyhs2x4ymnxl0b1zmdpzmm-python3-3.12.8-env/lib/python3.12/site-packages/hypothesis/strategies/_internal/core.py:1838
  /nix/store/jjfqmy1a6svyhs2x4ymnxl0b1zmdpzmm-python3-3.12.8-env/lib/python3.12/site-packages/hypothesis/strategies/_internal/core.py:1838: HypothesisDeprecationWarning: There is no reason to use @st.composite on a function which does not call the provided draw() function internally.
    note_deprecation(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
================ 44 passed, 1 warning in 2268.37s (0:37:48) ================

$ tree -L 2 tests
tests
├── test01e52
│   ├── data
│   ├── election.json
│   └── election.log
├── test02f73
│   ├── data
│   ├── election.json
│   └── election.log
├── ...
└── testf7ce1
    ├── data
    ├── election.json
    └── election.log

107 directories, 106 files
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

- [ ] Clearly separate Python scripts that run on the host vs in containers
- [ ] Should the host ones be a module with its own utils file?
- [ ] Go back to the [election](../election) and [verifier](../verifier) scripts
      and update them to match the latest code here in tests


## Out of scope for now

There are some parts of the election that aren't checked in the current implementation,
but seem important to me. They should be addressed in future work:

- [ ] admin can alter election constants without anyone noticing
- [ ] device can alter spoiled ballot nonces (presumably a voter's personal verifier would catch this!)
