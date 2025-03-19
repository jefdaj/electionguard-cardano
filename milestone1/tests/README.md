Test Script
===========

This script will generate arbitrary election configs, run the elections, and verify them.


## Generate random `election.json` configs

I'll start simple by just changing the numbers under `election`.
Then once that works I'll start making `votes` more flexible too.

```bash
$ nix develop

# sudo is required for now
# explicit random seed is optional
$ sudo TEST_RANDOM_SEED=1234 ./test.py

============================= test session starts ==============================
collecting ... collected 6 items

test.py::test_projectconfig_json_roundtrip <- config.py PASSED           [ 16%]
test.py::test_election_property_1 PASSED                                 [ 33%]
test.py::test_election_property_2 PASSED                                 [ 50%]
test.py::test_election_property_3 PASSED                                 [ 66%]
test.py::test_election_property_4 PASSED                                 [ 83%]
test.py::test_election_property_5 PASSED                                 [100%]

======================== 6 passed in 309.01s (0:05:09) =========================
```


## TODO

- [x] Have `verifier.py` send output to a log rather than printing if `--output` given
- [x] Set up the "generate config, run election, assert about results" loop
- [ ] Move `test.py` code -> `election.py`? or `conftest.py`?
- [ ] Re-learn some Hypothesis basics
- [ ] Rearrange `election.json`: "election" -> "roles", "votes" -> "contests", question inside contests
- [ ] Have `verifier.py` save a nested dict of all passing verifications in its json file
