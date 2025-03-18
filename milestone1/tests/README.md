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
$ sudo ./test.py

============================= test session starts ==============================
platform linux -- Python 3.12.8, pytest-8.3.3, pluggy-1.5.0
rootdir: /home/jefdaj/myrepos/electionguard-cardano/milestone1/tests
plugins: hypothesis-6.112.2
collected 1 item

config.py .                                                              [100%]

============================== 1 passed in 1.24s ===============================
```


## TODO

- [ ] Re-learn some Hypothesis basics
- [ ] Set up the "generate config, run election, assert about results" loop
- [x] Have `verifier.py` send output to a log rather than printing if `--output` given
- [ ] Rearrange `election.json`: "election" -> "roles", "votes" -> "contests", question inside contests
- [ ] Have `verifier.py` save a nested dict of all passing verifications in its json file
