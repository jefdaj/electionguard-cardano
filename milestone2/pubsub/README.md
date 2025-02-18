# pubsub

My first attempt at a non-trivial smart contract!
It'll focus on just distributing an authenticated log of files via Cardano + IPFS.
That's part of what the ElectionGuard contract will need to do,
as well as potentially useful on its own.

It will also confirm that TX fees can be funded from a pool in the contract.
That doesn't matter yet, but I want people to be able to post things for free
during an election.

TODO check whether there are any existing Cardano pubsub examples

## onchain code

- only one "publisher" role
- phase 1: open channel (contract), fund it with tADA
- phase 2: post one (many?) IPFS CIDs in a TX
    * repeat as needed
    * should also be able to top up the tAADA as needed
- phase 3: close channel and get remaining tADA back
- write in Aiken
- consider writing in Opshin too for comparison

## offchain code

- all apps run in docker containers
- each role managed by docker compose
- each participant should have network access to a cardano-node-ogmios instance
- publisher needs an address with tADA from the faucet
- publisher runs:
    * ipfs-cluster to pin CIDs when publishing them
    * a Python app to construct and submit TXs via PyCardano, control ipfs-cluster
- subscribers run:
    * Kupo to scan for published CIDs
    * an IPFS node (or single-node cluster?) to pin CIDs and fetch files
    * a Python app to keep a folder in sync with the channel, control IPFS + Kupo

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
