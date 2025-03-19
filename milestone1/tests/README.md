Test Script
===========

This script will generate arbitrary election configs, run the elections, and verify them.


## Generate random `election.json` configs

I'll start simple by just changing the numbers under `election`.
Then once that works I'll start making `votes` more flexible too.

```bash
$ nix develop

# haven't figured out how to create data dir with non-root permissions,
# so it only works as root for now
$ export TEST_RANDOM_SEED=1234
$ sudo ./test.py

============================= test session starts ==============================
platform linux -- Python 3.12.8, pytest-8.3.3, pluggy-1.5.0 -- /nix/store/f80kghwqd0gsf7p4maalc24lpx55ksw7-python3-3.12.8-env/bin/python3.12
cachedir: .pytest_cache
hypothesis profile 'default' -> database=DirectoryBasedExampleDatabase(PosixPath('/home/jefdaj/myrepos/electionguard-cardano/milestone1/tests/.hypothesis/examples'))
rootdir: /home/jefdaj/myrepos/electionguard-cardano/milestone1/tests
plugins: hypothesis-6.112.2
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

- [ ] Generate some elections as currently done first, then sample from them in other tests?
- [ ] Move `test.py` code -> `election.py`? or `conftest.py`?
- [ ] Re-learn some Hypothesis basics
- [ ] Set up the "generate config, run election, assert about results" loop
- [x] Have `verifier.py` send output to a log rather than printing if `--output` given
- [ ] Rearrange `election.json`: "election" -> "roles", "votes" -> "contests", question inside contests
- [ ] Have `verifier.py` save a nested dict of all passing verifications in its json file
