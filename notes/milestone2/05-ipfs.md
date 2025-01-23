# IPFS

Who hosts the IPFS data? My first (good) thought is that it should be `ipfs` instances for multiple networks, depending on config settings. So for example guardians might pin everything, becoming a kind of archive node. Mediators could keep everything they created as a backup. Observers might choose everything or only to cache what people request.

## Implementations

### Kubo

[Kubo](https://github.com/ipfs/kubo) seems a good default unless I end up having unusual requirements. They have [an API](https://docs.ipfs.tech/reference/kubo-rpc-cli/).

### Iroh

In case Kubo is slow or something, [Iroh](https://github.com/n0-computer/iroh) looks cool too.
Not sure whether I need the pub/sub things it offers yet, but speed is always nice!

... actually, [Iroh-Docs](https://www.iroh.computer/proto/iroh-docs) looks like it might be perfect? Investigate that a bit. The model of "one big replicated collection where each entry is signed by its author" is basically the same as I came up with for the MPT.

Not sure about the "namespace key" thing though. Maybe that makes it different enough not to be useful? Or maybe I can give the key to everyone in the smart contract? Or, maybe this isn't needed at all and vanilla IPFS with some syncing stuff would make more sense?

### [Helia](https://github.com/ipfs/helia)

Not sure where to get started yet, but worth trying.
[This](https://github.com/ipfs-examples/helia-examples/issues/306) is a little worrying though!

Maybe [here](https://github.com/ipfs-examples/helia-101)?

### IPFS Cluster

Ah, this is the one. [The docs](https://ipfscluster.io/documentation/quickstart/) are good and the example runs immediately.


## How to ensure no ballots get lost?

The main difficulty with IPFS is that no one guarantees a given file will be hosted and available.
I don't think solving that should be a focus of the initial demo, but later we'll need to ensure it with some incentives, double checking, or maybe outsourcing it to a protocol like FileCoin?

The simplest check I can think of is just to require that before a ballot moves from the message queue to the election record MPT, it's signed off on by N hosting parties. N can be configurable at the beginning of the election, and the hosting parties could be guardians, maybe with observers as a fallback later.

The only real downside to the sign-off idea is that it would multiply the number of transactions needed for the protocol by `N-1` (because the initial insert can come with one promise of availability).

Each voter who challenges or checks their vote should also be given a copy, of course.
And if the system ends up needing it, maybe they should be rewarded for having kept it and rescued the beaurocrats!
