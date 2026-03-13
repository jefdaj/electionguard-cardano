pubsub3
=======

This is the main codebase for all the M2 outputs.
It will have:

* [Documentation of the Aiken contract](./docs/smart-contract.md)
* An [election script](./election.sh) which uploads, downloads, and verifies in parallel

WARNING: on-chain code is currently ahead of off-chain; the two don't match yet

on-chain (Aiken) code
---------------------

Before running the main election script or tests,
you need to build the validator with Aiken.
There will be two versions of `plutus.json`: traced and production.
The Python code automatically uses the traced one when called via
pytest.

```
$ nix develop .#onchain
$ ./build.sh
+ set -e
++ dirname ./build.sh
+ cd .
+ aiken check --trace-level silent
    Compiling jefdaj/electionguard-cardano 0.1.0 (.)
    Compiling aiken-lang/stdlib 3.0.0 (./build/packages/aiken-lang-stdlib)
   Collecting all tests scenarios across all modules
      Testing ...

    ┍━ tests/integration/happy_adminchannel.tests ━━━━━━━━━━━━━━━━━━━━━━━
    │ PASS [mem: 280.31 K, cpu:  95.89 M] happy_adminchannel_initelection
    │ PASS [mem: 539.43 K, cpu: 182.51 M] happy_adminchannel_advancephase_2
    │ PASS [mem: 549.17 K, cpu: 185.45 M] happy_adminchannel_advancephase_3
    │ PASS [mem: 559.62 K, cpu: 188.58 M] happy_adminchannel_advancephase_4
    │ PASS [mem: 561.13 K, cpu: 188.56 M] happy_adminchannel_advancephase_5
    │ PASS [mem: 557.37 K, cpu: 187.29 M] happy_adminchannel_advancephase_6
    │ PASS [mem: 577.03 K, cpu: 193.89 M] happy_adminchannel_advancephase_7
    │ PASS [mem: 581.04 K, cpu: 194.60 M] happy_adminchannel_advancephase_8
    │ PASS [mem: 578.87 K, cpu: 193.41 M] happy_adminchannel_advancephase_9
    │ PASS [mem: 390.76 K, cpu: 129.35 M] happy_adminchannel_endelection
    ┕━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 10 tests | 10 passed | 0 failed

    ┍━ tests/integration/happy_election.tests ━━━━━━━━━━━━━━━━━━━━
    │ PASS [mem: 207.07 K, cpu:  68.69 M] happy_election_admin_tx0
    │ PASS [mem: 566.76 K, cpu: 190.02 M] happy_election_admin_tx1
    │ PASS [mem:   1.07 M, cpu: 355.12 M] happy_election_admin_tx2
    │ PASS [mem: 621.47 K, cpu: 205.83 M] happy_election_admin_tx3
    │ PASS [mem: 624.28 K, cpu: 207.16 M] happy_election_admin_tx4
    │ PASS [mem: 701.12 K, cpu: 234.92 M] happy_election_admin_tx5
    │ PASS [mem:   2.52 M, cpu: 722.94 M] happy_election_admin_tx6
    │ PASS [mem:   1.22 M, cpu: 395.26 M] happy_election_admin_tx7
    │ PASS [mem: 475.58 K, cpu: 161.07 M] happy_election_guardian1_tx1
    │ PASS [mem: 604.43 K, cpu: 204.59 M] happy_election_guardian1_tx2
    │ PASS [mem: 701.93 K, cpu: 238.63 M] happy_election_guardian1_tx3
    │ PASS [mem:   2.46 M, cpu: 710.35 M] happy_election_guardian1_tx4
    │ PASS [mem:   1.14 M, cpu: 376.63 M] happy_election_guardian1_tx5
    │ PASS [mem: 475.58 K, cpu: 161.07 M] happy_election_guardian2_tx1
    │ PASS [mem: 604.43 K, cpu: 204.59 M] happy_election_guardian2_tx2
    │ PASS [mem: 701.93 K, cpu: 238.63 M] happy_election_guardian2_tx3
    │ PASS [mem:   2.46 M, cpu: 710.35 M] happy_election_guardian2_tx4
    │ PASS [mem:   1.14 M, cpu: 376.63 M] happy_election_guardian2_tx5
    │ PASS [mem: 475.58 K, cpu: 161.07 M] happy_election_guardian3_tx1
    │ PASS [mem: 604.43 K, cpu: 204.59 M] happy_election_guardian3_tx2
    │ PASS [mem: 701.93 K, cpu: 238.63 M] happy_election_guardian3_tx3
    │ PASS [mem:   2.46 M, cpu: 710.35 M] happy_election_guardian3_tx4
    │ PASS [mem:   1.14 M, cpu: 376.63 M] happy_election_guardian3_tx5
    │ PASS [mem: 489.75 K, cpu: 164.32 M] happy_election_device1_tx1
    │ PASS [mem:   3.84 M, cpu:   1.05 B] happy_election_device1_tx2
    │ PASS [mem:   4.37 M, cpu:   1.22 B] happy_election_device1_tx3
    │ PASS [mem: 559.16 K, cpu: 182.91 M] happy_election_verifier1_tx1
    │ PASS [mem:   3.97 M, cpu:   1.32 B] happy_election_admin_tx8
    │ PASS [mem: 267.91 K, cpu:  86.86 M] happy_election_admin_tx9
    ┕━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 29 tests | 29 passed | 0 failed

    ┍━ tests/integration/happy_postpublicrecords.tests ━━━━━━━━━━━━━━━━
    │ PASS [mem: 551.23 K, cpu: 181.82 M] happy_postpublicrecords_admin
    │ PASS [mem: 440.21 K, cpu: 147.05 M] happy_postpublicrecords_subchannel
    ┕━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2 tests | 2 passed | 0 failed

    ┍━ tests/integration/happy_subchannel.tests ━━━━━━━━━━━━━━━━━━━━━
    │ PASS [mem: 660.11 K, cpu: 220.66 M] happy_subchannel_single_add
    │ PASS [mem:   1.04 M, cpu: 349.38 M] happy_subchannel_single_rm
    │ PASS [mem:   2.03 M, cpu: 661.27 M] happy_subchannel_multi_add
    │ PASS [mem:   7.50 M, cpu:   2.61 B] happy_subchannel_multi_rm
    ┕━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 4 tests | 4 passed | 0 failed

    ┍━ tests/unit/ballot_id.tests ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    │ PASS [mem:  59.42 K, cpu:  15.04 M] valid_hex_segment_test
    │ PASS [mem:  66.53 K, cpu:  16.85 M] invalid_hex_segment_test
    │ PASS [mem: 238.38 K, cpu:  59.94 M] valid_uuid_test
    │ PASS [mem: 247.53 K, cpu:  62.28 M] valid_ballot_id_test
    │ PASS [mem:   5.61 K, cpu:   1.36 M] invalid_prefix_test
    │ PASS [mem:  10.03 K, cpu:   2.51 M] invalid_format_test
    ┕━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 6 tests | 6 passed | 0 failed

    ┍━ tests/unit/cid.tests ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    │ PASS [mem: 964.12 K, cpu: 278.71 M] all_static_election_cids_valid
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
    ┕━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 14 tests | 14 passed | 0 failed

    ┍━ tests/unit/record.tests ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    │ PASS [mem:  13.11 M, cpu:   3.39 B] all_static_election_metadata_valid
    │ PASS [mem:  13.61 M, cpu:   3.52 B] all_static_election_records_valid
    ┕━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2 tests | 2 passed | 0 failed

    ┍━ tests/unit/stt.tests ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    │ PASS [mem: 108.75 K, cpu:  36.36 M] tx_sends_token_to_addr_valid
    ┕━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1 tests | 1 passed | 0 failed

      Summary 68 checks, 0 errors, 0 warnings
+ aiken build --out election-plutus.json
    Compiling jefdaj/electionguard-cardano 0.1.0 (.)
    Compiling aiken-lang/stdlib 3.0.0 (./build/packages/aiken-lang-stdlib)
   Generating project's blueprint (election-plutus.json)
      Summary 0 errors, 0 warnings
+ aiken build --out election-plutus-traced.json --trace-level verbose
    Compiling jefdaj/electionguard-cardano 0.1.0 (.)
    Compiling aiken-lang/stdlib 3.0.0 (./build/packages/aiken-lang-stdlib)
   Generating project's blueprint (election-plutus-traced.json)
      Summary 0 errors, 0 warnings
```

TODO:

* [x] plain CIDs -> records with metadata
* [x] custom STT names including election name + channel name (egc-test1234-admin-stt etc)
* [x] each subchannel has one authorized publisher for now
* [x] subchannels are just a different thing for now, rather than nested "regular" channels
* [x] admin is the only one who can close channels
* [x] contract includes minting + burning subchannels
* [x] all channels can be minted or burned at once (except admin)
* [x] contract has an explicit election step/stage/phase variable
* [ ] contract holds and distributes tADA to cover posting fees
* [ ] contract returns tADA to admin when closing main channel

off-chain (Python) code
-----------------------

TODO:

* [ ] add a "burn all tokens" action for use in testing
* [ ] manually construct pycardano txs for each step in an election
* [ ] have each container generate its own keypair
* [ ] all eg nodes share one cardano node for now
* [ ] share addrs with admin (via top level script and bind mounts for now)
* [ ] egsync should track and report election info: n each role, phase, n ballots, ...

The tests cover opening a new channel on testnet, publishing 0, 1, 2, or all
(81) static election artifacts from a previous election run, and closing the
channel. There's a [publisher](./offchain/pubsub/publisher.py) that submits
the transactions and a [subscriber](./offchain/pubsub/subscriber.py) that
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
