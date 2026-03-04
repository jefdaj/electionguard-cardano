pubsub3
=======

This is the main codebase for all the M2 outputs.
It will have:

* [Documentation of the Aiken contract](./pubsub3/docs/smart-contract.md)
* An [election script](./pubsub3/election.sh) which uploads, downloads, and verifies in parallel

WARNING: on-chain code is currently ahead of off-chain; the two don't match yet

on-chain code
-------------

TODO:

* [x] plain CIDs -> records with metadata
* [ ] custom STT names including election name + channel name (egc-test1234-admin-stt etc)
* [ ] contract includes minting + burning subchannels
* [ ] each subchannel has one authorized publisher for now
* [ ] admin is the only one who can close channels
* [ ] subchannels are just a different thing for now, rather than nested "regular" channels
* [ ] contract holds and distributes tADA to cover posting fees
* [ ] contract returns tADA to admin when closing main channel
* [ ] all channels can be minted or burned at once?
* [ ] contract has an explicit election step/stage/phase variable
* [ ] contract syncs main channel with subchannels on (some) transitions

Before running the main election script or tests,
you need to build the validator with Aiken.
There will be two versions of `plutus.json`: traced and production.
The Python code automatically uses the traced one when called via
pytest.

```
$ nix develop .#onchain
$ ./build.sh
++ dirname ./build.sh
+ cd .
+ aiken check
    Compiling jefdaj/electionguard-cardano 0.0.2 (.)
    Compiling aiken-lang/stdlib 3.0.0 (./build/packages/aiken-lang-stdlib)
   Collecting all tests scenarios across all modules
      Testing ...

    ┍━ election/ballot_id.tests ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    │ PASS [mem:  59.42 K, cpu:  15.04 M] valid_hex_segment_test
    │ PASS [mem:  66.53 K, cpu:  16.85 M] invalid_hex_segment_test
    │ PASS [mem: 238.38 K, cpu:  59.94 M] valid_uuid_test
    │ PASS [mem: 247.53 K, cpu:  62.28 M] valid_ballot_id_test
    │ PASS [mem:   5.61 K, cpu:   1.36 M] invalid_prefix_test
    │ PASS [mem:  10.03 K, cpu:   2.51 M] invalid_format_test
    ┕━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 6 tests | 6 passed | 0 failed

    ┍━ election/cid.tests ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    │ PASS [mem:   4.10 K, cpu:   1.02 M] valid_cid_test
    │ PASS [mem:   4.10 K, cpu:   1.02 M] valid_cid_different_hash_test
    │ PASS [mem:   4.10 K, cpu:   1.02 M] valid_cid_zeros_test
    │ PASS [mem:   2.50 K, cpu: 612.24 K] invalid_length_short_test
    │ PASS [mem:   2.50 K, cpu: 612.24 K] invalid_length_long_test
    │ PASS [mem:   3.20 K, cpu: 800.29 K] invalid_version_v0_test
    │ PASS [mem:   3.20 K, cpu: 800.29 K] invalid_version_v2_test
    │ PASS [mem:   4.60 K, cpu:   1.17 M] invalid_hash_type_test
    │ PASS [mem:   4.60 K, cpu:   1.17 M] invalid_hash_length_declaration_test
    │ PASS [mem:   2.50 K, cpu: 612.24 K] invalid_empty_cid_test
    │ PASS [mem:   3.90 K, cpu: 988.34 K] invalid_codec_test
    │ PASS [mem:   4.10 K, cpu:   1.02 M] valid_cid_min_values_test
    │ PASS [mem:   4.10 K, cpu:   1.02 M] valid_cid_max_hash_test
    ┕━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 13 tests | 13 passed | 0 failed

      Summary 19 checks, 0 errors, 0 warnings
+ aiken build --out election-plutus.json
    Compiling jefdaj/electionguard-cardano 0.0.2 (.)
    Compiling aiken-lang/stdlib 3.0.0 (./build/packages/aiken-lang-stdlib)
   Generating project's blueprint (election-plutus.json)
      Summary 0 errors, 0 warnings
+ aiken build --out election-plutus-traced.json --trace-level verbose
    Compiling jefdaj/electionguard-cardano 0.0.2 (.)
    Compiling aiken-lang/stdlib 3.0.0 (./build/packages/aiken-lang-stdlib)
   Generating project's blueprint (election-plutus-traced.json)
      Summary 0 errors, 0 warnings
```

off-chain code
--------------

TODO:

* [ ] have each container generate its own keypair
* [ ] all eg nodes share one cardano node for now
* [ ] share addrs with admin (via top level script and bind mounts for now)
* [ ] egsync should track and report election info: n each role, phase, n ballots, ...

The tests cover opening a new channel on testnet, publishing 0, 1, 2, or all
(81) static election artifacts from a previous election run, and closing the
channel. There's a [publisher](./offchain/pubsub/publisher.py) that submits
the transactions, a [validator](./onchain/validators/pubsub.ak) that checks
them on chain, and a [subscriber](./offchain/pubsub/subscriber.py) that
reconstructs them from the on-chain datums. Then the tests assert that the
reconstructed CID lists match the originals.

Before running them, make sure:

1. You have [Cardano node + Ogmios](../cardano-node-ogmios/) running and synced up
2. You've generated a keypair and funded it with tADA (see below)

```
$ nix develop .#offchain
$ python
Python 3.12.12 (main, Oct  9 2025, 11:07:00) [GCC 14.3.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import pubsub
>>> pubsub.generate_keys()

    Your new Preview testnet keys are here:

    /home/jefdaj/myrepos/electionguard-cardano/milestone2/pubsub3-aiken-pycardano-kupo/offchain/keys/pubsub3.sk
    /home/jefdaj/myrepos/electionguard-cardano/milestone2/pubsub3-aiken-pycardano-kupo/offchain/keys/pubsub3.addr

    Your public address (2nd file) is: addr_test1vr93qqyu30r5c7snd4wp8wu243st2xz8605yea78hgyg6uckjakk5

    Before continuing, fund that address with tADA from the faucet:
    https://docs.cardano.org/cardano-testnets/tools/faucet

    If you don't, local tests will still work but testnet tests will fail.

>>>
```

You can watch that address accumulate transactions on CardanoScan
during the tests if you want, and track mint + burn of various `pubsub3-channel-stt` tokens.

```
$ nix develop .#offchain
$ ./test.sh
+ EXTRA_ARGS=
+ pytest -vv
+ tee test.log
============================= test session starts ==============================
...
collecting ... collected 14 items

tests/test_publish_0.py::test_pub0_open PASSED                           [  7%]
tests/test_publish_0.py::test_pub0_closed PASSED                         [ 14%]
tests/test_publish_0.py::test_sub0_closed PASSED                         [ 21%]
tests/test_publish_1.py::test_pub1_open PASSED                           [ 28%]
tests/test_publish_1.py::test_pub1_closed PASSED                         [ 35%]
tests/test_publish_1.py::test_sub1_closed PASSED                         [ 42%]
tests/test_publish_2.py::test_pub2_open PASSED                           [ 50%]
tests/test_publish_2.py::test_pub2_closed PASSED                         [ 57%]
tests/test_publish_2.py::test_sub2_closed PASSED                         [ 64%]
tests/test_publish_all.py::test_sub_all_hist PASSED                      [ 71%]
tests/test_publish_all.py::test_pub_all_open PASSED                      [ 78%]
tests/test_publish_all.py::test_pub_all_closed PASSED                    [ 85%]
tests/test_publish_all.py::test_sub_all_closed PASSED                    [ 92%]
tests/test_records.py::test_load_election_records PASSED                 [100%]

======================== 14 passed in 810.86s (0:13:30) ========================
[INFO] [sub] Watcher thread exiting
```
