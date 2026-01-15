# pubsub2: post CIDs to preview testnet using ipfs, aiken, pycardano

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

All I've done so far are 2 minimal `testnet` tests, which post transactions
to the Preview network.

```python
@pytest.mark.testnet
@pytest.mark.slow
def test_publish_cids(ps: PubsubClient, cids: List[CIDv1]):

    # open channel
    open_tx = ps.open_channel()
    ps.wait_for_confirmation(open_tx)

    # publish cids
    pub1_tx = ps.publish_cids(cids)
    ps.wait_for_confirmation(pub1_tx)

    # again, to be sure chaining them works
    pub2_tx = ps.publish_cids(cids)
    ps.wait_for_confirmation(pub2_tx)

    # close channel
    close_tx = ps.close_channel()
    ps.wait_for_confirmation(close_tx)
```

```
$ nix develop .#offchain
$ ./test.sh 
+ EXTRA_ARGS=
+ pytest -vv
+ tee test.log
============================= test session starts ==============================
...
collecting ... collected 7 items

tests/test_publish.py::test_open PASSED                                  [ 14%]
tests/test_publish.py::test_close_nopub PASSED                           [ 28%]
tests/test_publish.py::test_publish_one PASSED                           [ 42%]
tests/test_publish.py::test_close_pub1 PASSED                            [ 57%]
tests/test_publish.py::test_publish_two PASSED                           [ 71%]
tests/test_publish.py::test_publish_all PASSED                           [ 85%]
tests/test_serialization.py::test_load_election_records PASSED           [100%]

======================== 7 passed in 838.54s (0:13:58) =========================

real    13m59.566s
user    0m19.783s
sys     0m0.290s
```

I'm planning to add some faster, simpler ones for things like round-tripping to
JSON too of course.

Format
------

Instead of `new_cids.txt`, this version will post CIDs on the preview testnet:

1. The publisher will construct transactions via PyCardano.
2. They'll be checked onchain by an Aiken validator.
3. Subscribers will get the CIDs via Kupo.


## Usage

```bash
./up.sh
arion logs --follow
```


## TODO

- [ ] publish lists/batches of "events" rather than CIDs: an event can be a subchannel open/close, or a public record
- [ ] publisher -> list of publishers, allowing a verifications channel?
- [ ] later, allow force inclusion of msgs signed by one of the publishers and submitted by any wallet
- [ ] are there any existing Cardano pubsub examples?
- [ ] should there be a channel NFT?
- [ ] is sending money to the validator an action, or separate?
- [ ] can tx fees can be funded from a pool in the contract?
- [ ] consider switching json encoder to [orjson](https://github.com/ijl/orjson)
- [ ] look into unixfs, dag, car stuff to sync directories
- [ ] look into the ipfs pubsub feature
- [ ] consider [ipfs-car-decoder](https://github.com/kralverde/py-ipfs-car-decoder/) for future voter verification app


## onchain code

- only one "publisher" role
- phase 1: open channel (publish validator), fund it with tADA
- phase 2: post one (many?) IPFS CIDs in a TX
    * repeat as needed
    * should also be able to top up the tADA as needed
- phase 3: close channel and get remaining tADA back
- write in Aiken
- consider writing in Opshin too for comparison

Opening a channel should mean both minting a channel NFT and funding it with
some tADA.

Posting files takes the channel NFT + old datum + tADA fund as input, returns
the NFT + remaining tADA + a new datum as outputs. The new datum will have a
list of the new CIDs. I don't think there's any need to keep old CIDs in the
current state, because Kupo or other indexers will be able to read the whole
history.

Topping up can be done just by sending tADA to the contract with no action?

Closing a channel should mean getting any remaining tADA back and burning the
NFT.


## offchain code

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
- TODO should the ipfs-cluster also be shared for now?



## Publisher

```bash
nix develop .#publisher

# to try new things before bothering to Nix package them
pip install -r requirements.txt

# safe to re-run, but only needs to be done once
# then send tADA from faucet -> keys/me.addr
./generate-keys.py
```


| Location | Purpose | Testing Strategy |
|----------|---------|------------------|
| **`pubsub/types/`** | PlutusData classes mirroring Aiken types | Unit tests verify serialization/deserialization |
| **`pubsub/builders/`** | Pure transaction construction functions | Unit tests inspect TransactionBuilder objects without submission |
| **`pubsub/utils/`** | Helper functions (keys, IPFS, serialization) | Unit tests with mocks |
| **`pubsub/client.py`** | High-level API combining all components | Integration tests using real blockchain |
| **`scripts/`** | Executable CLI tools using the client | Manual testing + optional integration tests |
| **`tests/unit/`** | Fast, pure logic tests (no I/O) | Run on every commit, part of Nix build |
| **`tests/integration/`** | Slow, blockchain-dependent tests | Run manually before releases |


## Additional Recommendations

### Use Type Hints Everywhere

PyCardano works great with mypy. Add to your dev dependencies:

```bash
pip install mypy
mypy offchain/pubsub --strict
```

Also Black?

TODO
----

1. **Set up the package structure** with `pyproject.toml` and empty `__init__.py` files
2. **Create your first Aiken type** (e.g., `ChannelDatum`) and its Python mirror
3. **Write unit tests** for that type's serialization
4. **Build a simple transaction builder** for publishing
5. **Add integration tests** once you have a deployed validator on Preview
6. **Create the client API** to tie everything together
7. **Write your CLI scripts** using the client

