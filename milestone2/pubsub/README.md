# pubsub

My first attempt at integrating the on-chain + off-chain code into a non-trivial dApp.
It'll focus on just distributing an authenticated log of files via Cardano + IPFS.
That's part of what the ElectionGuard contract will need to do,
as well as potentially useful on its own.


## Setup

```bash
# start everything
nix develop
arion up -d
```


```bash
# tail logs
nix develop
arion logs --follow
```

## IPFS

TODO update ip addrs here once stable

```bash
# ipfs

# apis are on ports 5001, 5002, ...
curl -X POST http://127.0.0.1:5001/api/v0/swarm/peers

# http is on ports 8081, 8082, ...
curl "http://127.0.0.1:8081/ipfs/bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi" > cat.jpg
```

`dweb.link` appears to be a good current gateway in case users need one.
Construct URLs like: <https://dweb.link/ipfs/MYCID>
They appear to work immediately, at least with the tiny test JSON files.

The officially recommended
[ipfs-http-client](https://github.com/ipfs-shipyard/py-ipfs-http-client) is
abandoned, but [aioipfs](https://gitlab.com/cipres/aioipfs) works great!

```bash
cd publisher # or subscriber
nix develop
pip install -r requirements.txt
```


## IPFS via Python

```bash
$ cd publisher
$ nix develop

$ # upload a json file, embedding the public path in it
$ ./ipfs-upload.py
Actual path to a JSON file to upload: ../../../milestone1/local-election/data/public/1_config/1_announce/1_manifest.json
Path to put in IPFS JSON data: 1_config/1_announce/1_manifest
QmZ4EzZfUvrHDtZFw7HC2zcX9HGKpwHrZYzgTPbGigdGqj
Actual path to a JSON file to upload: ^C
ok, done

```

```bash
$ cd subscriber
$ nix develop

$ # download it from other ipfs instance
$ ./ipfs-download.py
Next CID to download: QmZ4EzZfUvrHDtZFw7HC2zcX9HGKpwHrZYzgTPbGigdGqj
wrote QmZ4EzZfUvrHDtZFw7HC2zcX9HGKpwHrZYzgTPbGigdGqj to ./data/1_config/1_announce/1_manifest.json
Next CID to download: ^C
ok, done

$ cat ./data/1_config/1_announce/1_manifest.json | jq | head
{
  "election_scope_id": "electionguard-cardano-test-manifest",
  "spec_version": "1.0",
  "type": "general",
  "start_date": "2025-02-25T15:20:54.121535",
  "end_date": "2025-02-28T03:20:54.121535",
  "geopolitical_units": [
    {
      "object_id": "electionguard-cardano-test-county",
      "name": "ElectionGuard + Cardano Test County",
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


## versions

- one where it runs locally and they share a node
- one using 2 computers and a node each


## literature

- blog post
- asciinema demo of the local version
- video of the local + 2 computer versions


## file formats

- all posts are JSON, but there's no way to validate that on chain right?
- top level fields: relative path from root dir, further content
- that way the sync app can maintain the folder in an easy, human readable way
- reusing a path replaces it in the sync folder
- no way to delete? maybe add that for the folder sync use case
- publisher's signature and date posted come from TX info, not JSON


## interfaces

- simple Python CLI per role: publisher, subscriber
- subscriber will need to type in the contract address, time to scan from
    * can those be combined in one QR code?
    * default to date I wrote this if none given


## Mint TXs with IPFS links

I was about to try to query Kupo for NFTs, get their IPFS CIDs, and pin them.
But then I realized I don't actually need to be minting NFTs; a simpler custom
metadata would work unless/until I end up wanting actual NFTs.  That means I
need to start minting my own things though, rather than querying existing NFT
collections...

TODO:

- Should I follow [the CIP-10 metadata registry testnet](https://github.com/input-output-hk/metadata-registry-testnet) format?
