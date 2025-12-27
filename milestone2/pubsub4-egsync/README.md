pubsub4: election via IPFS + JSON channels
==========================================

This is an elaboration on [pubsub1-ipfs](../pubsub1-ipfs) that will minimize
the shared public state, replacing it with just a set of JSONL files that
mock pubsub channel smart contracts. Each ElectionGuard role will be paired
with an IPFS node and will keep its own view of the global state based on
messages posted to the "onchain" channels.

Shared state
------------

Instead of `data/public`, each ElectionGuard role will have its own separate
set of IPFS files reconstructed from "onchain" JSON messages, like this:

```
data/
├── onchain
│   ├── admin_1.jsonl
│   ├── device_1.jsonl
│   ├── guardian_1.jsonl
│   └── verifier_1.jsonl
└── private
    ├── admin_1
    ├── device_1
    │   ├── egsync
    │   │   ├── 1_config
    │   │   │   ├── 1_announce
    │   │   │   ├── 2_ceremony
    │   │   │   ├── 3_election
    │   │   │   └── 4_devices
    │   │   ├── 2_ballots
    │   │   │   ├── 1_submitted
    │   │   │   ├── 2_cast
    │   │   │   └── 3_spoiled
    │   │   └── 3_results
    │   │       ├── 1_shares
    │   │       ├── 2_combined
    │   │       └── 3_summary.json
    │   └── tmp
    │       ├── logs
    │       │   ├── attack.log
    │       │   └── verify.log
    │       └── plaintext_ballots
    │           ├── ballot-16fa6ff6-e119-11f0-9481-4210f8977e3d.json
    │           ├── ballot-191a24fc-e119-11f0-ac7d-4210f8977e3d.json
    │           └── ballot-1b2c94fa-e119-11f0-92f5-4210f8977e3d.json
    ├── guardian_1
    └── verifier_1
```

Message format
--------------

One of the main points of this exercise is to refine the format.
So far I'm thinking:

- channel is a JSONL opened append-only
- each append corresponds to a UTXO
- generic message types: `open_channel`, `close_channel`, `post_public_records` (a list of public record messages)
- public record message types:

    * match current `to_public_record` calls in Python code
    * except that the file content is replaced with a CID
- maybe also `authorize_channel` for admin to authorize the guardians + devices + official verifiers to post
  (later, should include a public option for anyone to post disputes and verifications)
- and `add_relay` + `remove_relay` for the admin to optionally say where they'll be serving the IPFS files from
  (either a self hosted ipfs-cluster or pinning service, probably)

egsync
------

Maybe it's time to start the egsync container(s) and have the ElectionGuard ones communicate with them via an API?
It can be a subscriber all the time and also publish things when requested to.
It could have a very simple API for now:

- post `to_public_record`
- get `from_public_record`

The mapping of those calls <--> filenames can be moved from utils to the new egsync.

TODO
----

How should attacks work in this version? Will we need a different way than editing files in place? Or maybe have attacks override the immutability in egsync?
