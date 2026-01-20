pubsub2: post CIDs to preview testnet
=====================================

Instead of `new_cids.txt`, this version posts CIDs on the preview testnet:

1. The publisher constructs transactions via PyCardano.
2. They're checked onchain by the Aiken validator.
3. Subscribers fetch CIDs via Kupo.

It's not one of the milestone deliverables, so it doesn't need a standalone main script.
Instead it just tests each component with pytest.

Build
-----

Before running the tests, you need to build the validator with Aiken.
There will be two versions of `plutus.json`: traced and production.
The Python code automatically uses the traced one when called via
pytest.

```
$ nix develop .#onchain
$ ./build.sh
++ dirname ./build.sh
+ cd .
+ aiken build --out pubsub2-plutus.json
    Compiling jefdaj/electionguard-cardano-pubsub2 0.0.1 (.)
    Compiling aiken-lang/stdlib 3.0.0 (./build/packages/aiken-lang-stdlib)
   Generating project's blueprint (pubsub2-plutus.json)
      Summary 0 errors, 0 warnings
+ aiken build --out pubsub2-plutus-traced.json --trace-level verbose
    Compiling jefdaj/electionguard-cardano-pubsub2 0.0.1 (.)
    Compiling aiken-lang/stdlib 3.0.0 (./build/packages/aiken-lang-stdlib)
   Generating project's blueprint (pubsub2-plutus-traced.json)
      Summary 0 errors, 0 warnings
```

Test
----

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

    /home/jefdaj/myrepos/electionguard-cardano/milestone2/pubsub2-aiken-pycardano-kupo/offchain/keys/pubsub2.sk
    /home/jefdaj/myrepos/electionguard-cardano/milestone2/pubsub2-aiken-pycardano-kupo/offchain/keys/pubsub2.addr

    Your public address (2nd file) is: addr_test1vr93qqyu30r5c7snd4wp8wu243st2xz8605yea78hgyg6uckjakk5

    Before continuing, fund that address with tADA from the faucet:
    https://docs.cardano.org/cardano-testnets/tools/faucet

    If you don't, local tests will still work but testnet tests will fail.

>>> 
```

You can watch that address accumulate transactions on CardanoScan or ADAstat
during the tests if you want, and track mint + burn of various `pubsub2-channel-stt` tokens.

```
$ nix develop .#offchain
$ ./test.sh 
============================= test session starts ==============================

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

======================== 14 passed in 587.18s (0:09:47) ========================
```
