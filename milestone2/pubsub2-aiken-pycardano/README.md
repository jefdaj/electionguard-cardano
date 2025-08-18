# pubsub2: post CIDs to preview testnet using ipfs, aiken, pycardano


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


## Aiken

Write validators in the `validators` folder, and supporting functions in the `lib` folder using `.ak` as a file extension.

```aiken
validator my_first_validator {
  spend(_datum: Option<Data>, _redeemer: Data, _output_reference: Data, _context: Data) {
    True
  }
}
```

### Building

```sh
aiken build
```

### Configuring

**aiken.toml**
```toml
[config.default]
network_id = 41
```

Or, alternatively, write conditional environment modules under `env`.

### Testing

You can write tests in any module using the `test` keyword. For example:

```aiken
use config

test foo() {
  config.network_id + 1 == 42
}
```

To run all tests, simply do:

```sh
aiken check
```

To run only tests matching the string `foo`, do:

```sh
aiken check -m foo
```

### Documentation

If you're writing a library, you might want to generate an HTML documentation for it.

Use:

```sh
aiken docs
```

### Resources

Find more on the [Aiken's user manual](https://aiken-lang.org).
