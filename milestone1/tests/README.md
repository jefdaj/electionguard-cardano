Test Script
===========

This script will generate arbitrary election configs, run the corresponding
test elections, and verify some properties of the output files. The elections
can be slow, but it caches the output files so at least editing and re-running
the property tests is fast.

```bash
# run a single test election as before in ../election

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

```bash
# generate 10 arbitrary configs,
# run the corresponding elections,
# and check properties of their data files

$ nix develop

# explicit random seed is optional
# sudo is required to work around docker bind mount permission errors
$ sudo TEST_RANDOM_SEED=1234 ./test.py

============================= test session starts ==============================
...
collecting ... collected 11 items

test.py::test_roundtrip_arionconfig PASSED                               [  9%]
test.py::test_roundtrip_voteconfig PASSED                                [ 18%]
test.py::test_roundtrip_contestconfig PASSED                             [ 27%]
test.py::test_roundtrip_electionconfig PASSED                            [ 36%]
test.py::test_roundtrip_projectconfig PASSED                             [ 45%]
test.py::test_election_finished PASSED                                   [ 54%]
test.py::test_election_verified_by_admin PASSED                          [ 63%]
test.py::test_all_election_verifiers_agree PASSED                        [ 72%]
test.py::test_n_verifications_matches_cfg PASSED                         [ 81%]
test.py::test_cast_votes_match_config PASSED                             [ 90%]
test.py::test_spoiled_votes_match_config PASSED                          [100%]

...
======================== 11 passed, 1 warning in 2.46s =========================

```


## TODO

- [x] Re-learn some Hypothesis basics
- [x] Have `verifier.py` send output to a log rather than printing if `--output` given
- [x] Set up the "generate config, run election, assert about results" loop
- [x] Rearrange `election.json`: "election" -> "roles", "votes" -> "contests", question inside contests
- [x] Have `verifier.py` save a nested dict of all passing verifications in its json file
- [ ] Move `test.py` code -> `election.py`? or `conftest.py`?
