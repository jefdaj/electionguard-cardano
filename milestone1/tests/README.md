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

=================================== test session starts ====================================
platform linux -- Python 3.12.8, pytest-8.3.3, pluggy-1.5.0 -- /nix/store/f80kghwqd0gsf7p4maalc24lpx55ksw7-python3-3.12.8-env/bin/python3.12
cachedir: .pytest_cache
hypothesis profile 'default' -> database=DirectoryBasedExampleDatabase(PosixPath('/home/jefdaj/myrepos/electionguard-cardano/milestone1/tests/.hypothesis/examples'))
rootdir: /home/jefdaj/myrepos/electionguard-cardano/milestone1/tests
plugins: hypothesis-6.112.2
collected 9 items

test.py::test_roundtrip_arionconfig PASSED                                           [ 11%]
test.py::test_roundtrip_voteconfig PASSED                                            [ 22%]
test.py::test_roundtrip_votesconfig PASSED                                           [ 33%]
test.py::test_roundtrip_electionconfig PASSED                                        [ 44%]
test.py::test_roundtrip_projectconfig PASSED                                         [ 55%]
test.py::test_election_finished PASSED                                               [ 66%]
test.py::test_election_verified_by_admin PASSED                                      [ 77%]
test.py::test_all_election_verifiers_agree PASSED                                    [ 88%]
test.py::test_n_verifications PASSED                                                 [100%]

========================= 9 passed, 1 warning in 912.84s (0:15:12) =========================
```


## TODO

- [x] Re-learn some Hypothesis basics
- [x] Have `verifier.py` send output to a log rather than printing if `--output` given
- [x] Set up the "generate config, run election, assert about results" loop
- [ ] Move `test.py` code -> `election.py`? or `conftest.py`?
- [ ] Rearrange `election.json`: "election" -> "roles", "votes" -> "contests", question inside contests
- [ ] Have `verifier.py` save a nested dict of all passing verifications in its json file
