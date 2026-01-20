pubsub2: post CIDs to preview testnet
=====================================

Instead of `new_cids.txt`, this version posts CIDs on the preview testnet:

1. The publisher constructs transactions via PyCardano.
2. They're checked onchain by the Aiken validator.
3. Subscribers fetch CIDs via Kupo.

Build
-----

There are two versions of `plutus.json`: traced and production.
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

onchain code
------------

- only one "publisher" role
- phase 1: open channel (publish validator), fund it with tADA
- phase 2: post a batch of IPFS CIDs in a TX
    * repeat as needed
    * should also be able to top up the tADA as needed
- phase 3: close channel and get remaining tADA back

Opening a channel means minting a channel NFT and funding it with some tADA.

Posting files takes the channel NFT + old datum + tADA fund as input, returns
the NFT + remaining tADA + a new datum as outputs. The new datum will have a
list of the new CIDs.

Topping up can be done just by sending tADA to the contract with no action?

Closing a channel means getting any remaining tADA back and burning the
NFT.

offchain code
-------------

- all apps run in docker containers
- containers are managed by one top level arion-compose file
- each participant should have network access to a shared cardano-node-ogmios instance
- publisher needs an address with tADA from the faucet
- publisher runs:
    * ipfs-cluster to pin CIDs when publishing them
    * a Python app to construct and submit TXs via PyCardano, control ipfs-cluster
- subscribers run:
    * Kupo to scan for published CIDs
    * an IPFS node (or single-node cluster?) to pin CIDs and fetch files
    * a Python app to keep a folder in sync with the channel, control IPFS + Kupo
- should the ipfs-cluster also be shared for now?
