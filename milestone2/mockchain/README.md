mockchain
=========

This is part of [pubsub4-egsync](../pubsub4-egsync).
I split it out into a separate mini dev environment because it was starting to
get complicated working on this + the new "triplet" node design (an egpy +
egsync + ipfs container per electionguard role).

JSON files
----------

The idea is to elaborate `new_cids.txt` from [pubsub1-ipfs](../pubsub1-ipfs)
into a directory of JSON files that can represent all the details I want to put
in the smart contract protocol.

So far I'm thinking it'll look like:

```
mockchain/
├── admin
│   ├── 0001.json
│   ├── 0002.json
│   ├── 0003.json
│   ├── 0004.json
│   └── 0005.json
├── device1
│   └── 0001.json
├── guardian1
│   ├── 0001.json
│   └── 0002.json
├── guardian2
│   ├── 0001.json
│   └── 0002.json
└── public
    └── 0001.json
```

The subfolders are pubsub channels corresponding to state NFTs.  Each
election starts with just an `admin` channel, then the admin publishes
`new_channel` messages (mints NFTs) authorizing others to post. Each channel
will be single-threaded for now because I don't expect throughput to be a
problem any time soon.

Besides the channel open/close messages, most of what gets posted will be
`post_public_record` messages like this:

```json
{
  "action": "post_public_record",
  "record_type": "manifest",
  "cid": "QmdCbkQ53MBNXpPhFeeNBEd3QEti6yQ7FqoyLiGyGjwvdh"
}
```

They'll contain info for fetching the election artifacts over IPFS and
assembling them into the standard tree of file we've been looking at so far.
