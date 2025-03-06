Verifier Script
===============

This verifies the results of the [local election script](../local-election).

TODO:

- [ ] Monkey patch the electionguard LOG to throw exceptions during verification
      (because throwing them all the time messes with the test suite)
- [ ] Make a JSON summary of the verification as well as printing
- [ ] Have this script create the summary json rather than the admin?

Example output so far:

```bash
$ nix develop
$ ./verify.py

docker exec verifier-verifier1-1 poetry run /scripts/verifier.py verify --public-dir /data/public

verifying the ciphertext of the 6 cast ballots:
  ballot-557762aa-fab7-11ef-80d6-0242ac120006... ok
  ballot-578663ca-fab7-11ef-9526-0242ac120006... ok
  ballot-599b493c-fab7-11ef-8aba-0242ac120006... ok
  ballot-54f69c1a-fab7-11ef-8746-0242ac120004... ok
  ballot-57032910-fab7-11ef-bd39-0242ac120004... ok
  ballot-5470327e-fab7-11ef-8ae4-0242ac120008... ok

verifying the ciphertext of the 6 spoiled ballots:
  ballot-567f7d40-fab7-11ef-a62d-0242ac120008... ok
  ballot-55fa190c-fab7-11ef-b966-0242ac120005... ok
  ballot-588d02c4-fab7-11ef-bb8a-0242ac120008... ok
  ballot-580a3e98-fab7-11ef-8763-0242ac120005... ok
  ballot-53e938fa-fab7-11ef-bcc5-0242ac120005... ok
  ballot-5914e0e0-fab7-11ef-8983-0242ac120004... ok
```

And if I manually edit one of the ciphertexts:

```
verifying that all ballots are accounted for:
  6 ballots cast + 6 spoiled = 12 submitted... ok
  set(cast IDs) + set(spoiled IDs) = set(submitted IDs)... ok

verifying the ciphertext of the 6 cast ballots:
  ballot-557762aa-fab7-11ef-80d6-0242ac120006... ok
  ballot-578663ca-fab7-11ef-9526-0242ac120006... ok
  ballot-599b493c-fab7-11ef-8aba-0242ac120006... ok
  ballot-54f69c1a-fab7-11ef-8746-0242ac120004... ok
  ballot-57032910-fab7-11ef-bd39-0242ac120004... ok
  ballot-5470327e-fab7-11ef-8ae4-0242ac120008... ok

verifying the ciphertext of the 6 spoiled ballots:
  ballot-567f7d40-fab7-11ef-a62d-0242ac120008... ok
  ballot-55fa190c-fab7-11ef-b966-0242ac120005... FAIL
  ballot-588d02c4-fab7-11ef-bb8a-0242ac120008... ok
  ballot-580a3e98-fab7-11ef-8763-0242ac120005... ok
  ballot-53e938fa-fab7-11ef-bcc5-0242ac120005... ok
  ballot-5914e0e0-fab7-11ef-8983-0242ac120004... ok

ERROR Found 1 irregularities...

{
  "spoiled_ballots": {
    "ballot-55fa190c-fab7-11ef-b966-0242ac120005": "ballot.py.is_valid_encryption:#L201: mismatching crypto hash: referendum-pineapple-affirmative-selection expected(920BA11D5357F8B7563D1E6ED20CC97246C9856106E80B812DA2CEDD6572EA16), actual(AA2906CD7AAB1E74946895EFDBF0E414678152E3FA425289F5301DD573BA83FC)\nballot.py.is_valid_encryption:#L591: ciphertext does not equal elgamal accumulation for : referendum-pineapple"
  }
}

The election should NOT be certified!
```

And if I remove a file:

```
verifying that all ballots are accounted for:
  Unable to check ballot IDs because cast_ballots failed to load

verifying the ciphertext of the 6 spoiled ballots:
  ballot-567f7d40-fab7-11ef-a62d-0242ac120008... ok
  ballot-55fa190c-fab7-11ef-b966-0242ac120005... ok
  ballot-588d02c4-fab7-11ef-bb8a-0242ac120008... ok
  ballot-580a3e98-fab7-11ef-8763-0242ac120005... ok
  ballot-53e938fa-fab7-11ef-bcc5-0242ac120005... ok
  ballot-5914e0e0-fab7-11ef-8983-0242ac120004... ok

Unable to finish running the verification.
ERROR Found 1 irregularities...

{
  "cast_ballots": {
    "load_cast_ballots": "[Errno 2] No such file or directory: '/data/public/2_ballots/1_submitted/ballot-5470327e-fab7-11ef-8ae4-0242ac120008.json'"
  }
}

The election should NOT be certified!
```
