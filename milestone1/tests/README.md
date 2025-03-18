Test Script
===========

This script will generate arbitrary election configs, run the elections, and verify them.

TODO:

- [x] Have `verifier.py` send output to a log rather than printing if `--output` given
- [ ] Rearrange `election.json`: "election" -> "roles", "votes" -> "contests", question inside contests
- [ ] Have `verifier.py` save a nested dict of all passing verifications in its json file
