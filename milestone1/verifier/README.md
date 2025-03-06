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

checking that all ballots are accounted for:
  6 ballots cast + 6 spoiled = 12 submitted... ok
  set(cast IDs) + set(spoiled IDs) = set(submitted IDs)... ok

verifying the ciphertext of the 6 cast ballots:
  ballot-21e37226-f38c-11ef-b7ff-0242ac140006... ok
  ballot-26bb5bc4-f38c-11ef-82f8-0242ac140007... ok
  ballot-244a9242-f38c-11ef-8e96-0242ac140008... ok
  ballot-22dbdd9e-f38c-11ef-b4ba-0242ac140007... ok
  ballot-24c6b4a8-f38c-11ef-bf9a-0242ac140007... ok
  ballot-226159de-f38c-11ef-94a1-0242ac140008... ok

verifying the ciphertext of the 6 spoiled ballots:
  ballot-235283ea-f38c-11ef-91fa-0242ac140004... ok
  ballot-263fd22e-f38c-11ef-b322-0242ac140008... ok
  ballot-25c027cc-f38c-11ef-949b-0242ac140006... ok
  ballot-216af0b2-f38c-11ef-83ff-0242ac140004... ok
  ballot-23cf5780-f38c-11ef-b600-0242ac140006... ok
  ballot-2541cb0c-f38c-11ef-8f7f-0242ac140004... ok
```

And if I manually edit one of the ciphertexts:

```
...

verifying the ciphertext of the 6 spoiled ballots:
  ballot-235283ea-f38c-11ef-91fa-0242ac140004... ok
  ballot-263fd22e-f38c-11ef-b322-0242ac140008... ok
  ballot-25c027cc-f38c-11ef-949b-0242ac140006... ok
  ballot-216af0b2-f38c-11ef-83ff-0242ac140004... ok
  ballot-23cf5780-f38c-11ef-b600-0242ac140006... [8:2025-03-06 01:06:48,926]:WARNING:ballot.py.is_valid_encryption:#L201: mismatching crypto hash: referendum-pineapple-affirmative-selection expected(060A0951838584221D643D3FD25110B91570B2C15E5094EF5DE44138936E3669), actual(A6775F6E69EB1A2953D5EB832EEAF3DC77964BAAE096100CEE6363460525F0E3)
[8:2025-03-06 01:06:48,974]:WARNING:ballot.py.is_valid_encryption:#L591: ciphertext does not equal elgamal accumulation for : referendum-pineapple
ERROR ballot-23cf5780-f38c-11ef-b600-0242ac140006 failed verification!
  ballot-2541cb0c-f38c-11ef-8f7f-0242ac140004... ok

ERROR 1 ballots failed verification
election should NOT be certified
```
