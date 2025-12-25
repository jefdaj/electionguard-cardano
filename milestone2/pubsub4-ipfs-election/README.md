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
    │   ├── ipfs
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
