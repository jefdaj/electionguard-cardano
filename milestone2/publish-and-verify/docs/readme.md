# Tour of the electionguard-cardano validator code

In this first MVP version of the ElectionGuard + Cardano system, the on-chain code serves two purposes, both related to limiting the power of the government (AKA election administrator) by decentralizing some of their duties:

1. The contract acts as the "public, append-only bulletin board". In traditional non-blockchain ElectionGuard deployments, this would just be website. Decentralizing it removes the temptation for the admin to alter records or take the site down if they don't like how the election is going, and reduces their exposure to being hacked or DDoSed.

2. The contract also makes it easier for the head administrator to delegate authority. Instead of one monolithic "election system" the public can see the admin assigning other keys to particular roles (guardian, ballot encryption device, official verifier) and knows which one(s) signed each election artifact.

There are many other things the blockchain would also be useful for, but they're left for future versions:

- uncensorable disputes and transparent dispute resolution
- provably random (unbiased) risk-limiting audits
- collateral/slashing to improve trust in election officials
- incentives for 3rd parties to host and serve data
- ...

## Visualizing the on-chain data

Cardano smart contracts can be tricky to visualize because they don't construct transactions; they only decide whether a given transaction made by off-chain code is valid or not. So the simplest way to start is with an example of the data structure they're trying to force the off-chain code to create.

In this case it's a multithreaded pubsub channel:

![](./fig01.svg)

There's always one admin channel with an associated state thread token (STT). The admin can mint and burn subchannel tokens. Each subchannel has one authorized publisher, who can update its state to post public records. The admin can post records on their own channel too, as well as update a couple extra bits of admin state.

## Public Records

Leaving the admin channel aside for a minute, most transactions are simple: one of the subchannel publishers posts a list of public records to their channel. In the case of a ballot encryption device, the list might look like:

```aiken
[
  PublicRecord {
    ipfs_cid: #"0155122023f9c548fcfc4d6cab3665aea8c1d4ab436cf284f34148cc8c32f3f0cff5b166",
    metadata: BallotSubmitted {
      ballot_id: to_bytearray(@"ballot-4b4fb8a6-1d64-11f1-a997-768fd7ed4145")
    }
  },
  PublicRecord {
    ipfs_cid: #"0155122017fd845417e179f8a0f8bb69fca3b3c428a14a97b3d6fc982390a372275acfcb",
    metadata: BallotSubmitted {
      ballot_id: to_bytearray(@"ballot-4c9f842a-1d64-11f1-94d0-768fd7ed4145")
    }
  },
  PublicRecord {
    ipfs_cid: #"01551220b2fe6231a43ea31a09df0e6277e8ebca319e77f089fa169053a264b6a9d13b9b",
    metadata: BallotSpoiled {
      ballot_id: to_bytearray(@"ballot-48b5dc74-1d64-11f1-9b1b-768fd7ed4145")
    }
  },
  PublicRecord {
    ipfs_cid: #"01551220f9bba653cd2cd599b0d83ae8965b7596dfc5875e2eee3161f0db89367f1c10e5",
    metadata: CastNotice {
      ballot_id: to_bytearray(@"ballot-4957f5fe-1d64-11f1-9226-768fd7ed4145")
    }
  }
]
```

That's two newly scanned ballots being submitted, one previously submitted ballot being "spoiled" (AKA audited or marked for public decryption) by the voter, and one previously submitted ballot being cast by the voter.

To prevent unnecessary chain bloat, each update only includes the latest batch of `new_records`; to get the full history you need to run a blockchain indexer.

## Election Phases
