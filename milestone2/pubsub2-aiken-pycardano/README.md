# pubsub2: post CIDs to preview testnet using ipfs, aiken, pycardano

Tests
-----

The `testnet` tests will actually post Preview network transactions.
For example this one...

```
$ ./test.sh 
+ EXTRA_ARGS=
+ pytest
+ tee test.log
============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-8.3.5, pluggy-1.5.0
rootdir: /home/jefdaj/myrepos/electionguard-cardano/milestone2/pubsub2-aiken-pycardano/offchain
configfile: pyproject.toml
plugins: typeguard-4.4.2
collected 1 item

tests/testnet/test_publish.py .                                          [100%]

============================== 1 passed in 43.64s ==============================
```

... [minted](https://preview.cardanoscan.io/transaction/7ed43c6d4122f20946fc9a322e42d1aeb390806fc7e8f7efb379384747c0fbe1?tab=tokenmint)
a state thread token and then
[burned it](https://preview.cardanoscan.io/transaction/a8ca16af59691e2c81a5755afd04f0c5ff98d6edb3a9cfb5837b93dfead00af4?tab=tokenmint).


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

