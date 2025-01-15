# IPFS

Who hosts the IPFS data? My first (good) thought is that it should be `ipfs` instances for multiple networks, depending on config settings. So for example guardians might pin everything, becoming a kind of archive node. Mediators could keep everything they created as a backup. Observers might choose everything or only to cache what people request.

## Kubo

[Kubo](https://github.com/ipfs/kubo) seems a good default unless I end up having unusual requirements. They have [an API](https://docs.ipfs.tech/reference/kubo-rpc-cli/).

## Iroh

In case Kubo is slow or something, [Iroh](https://github.com/n0-computer/iroh) looks cool too.
Not sure whether I need the pub/sub things it offers yet, but speed is always nice!

## How to ensure no ballots get lost?

The main difficulty with IPFS is that no one guarantees a given file will be hosted and available.
I don't think solving that should be a focus of the initial demo, but later we'll need to ensure it with some incentives, double checking, or maybe outsourcing it to a protocol like FileCoin?

The simplest check I can think of is just to require that before a ballot moves from the message queue to the election record MPT, it's signed off on by N hosting parties. N can be configurable at the beginning of the election, and the hosting parties could be guardians, maybe with observers as a fallback later.
