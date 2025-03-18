Test Script
===========

This script will generate arbitrary election configs, run the elections, and verify them.


## Generate random `election.json` configs

Here's what the one from the [election script](../election) looks like:

```json
{
  "arion": {
    "project_name": "test",
    "bind_mounts": {
      "scripts": "/scripts",
      "public": "/data/public",
      "private": "/data/private"
    }
  },
  "election": {
    "guardians": {"count": 3, "quorum": 2},
    "devices": {"count": 4},
    "verifiers": {"count": 2},
    "question": "Are pineapples cool?"
  },
  "votes": {
    "Yes":    {"cast": 3, "spoil":1},
    "No":     {"cast": 2, "spoil":2},
    "Unsure": {"cast": 1, "spoil":3}
  }
}
```

I'll start simple by just changing the numbers under `election`.
Then once that works I'll start making `votes` more flexible too.


## TODO

- [ ] Re-learn some Hypothesis basics
- [ ] Set up the "generate config, run election, assert about results" loop
- [x] Have `verifier.py` send output to a log rather than printing if `--output` given
- [ ] Rearrange `election.json`: "election" -> "roles", "votes" -> "contests", question inside contests
- [ ] Have `verifier.py` save a nested dict of all passing verifications in its json file
