# IPFS

Who hosts the IPFS data? My first (good) thought is that it should be `ipfs` instances for multiple networks, depending on config settings. So for example guardians might pin everything, becoming a kind of archive node. Mediators could keep everything they created as a backup. Observers might choose everything or only to cache what people request.

## Kubo

[Kubo](https://github.com/ipfs/kubo) seems a good default unless I end up having unusual requirements. They have [an API](https://docs.ipfs.tech/reference/kubo-rpc-cli/).

## Iroh

In case Kubo is slow or something, [Iroh](https://github.com/n0-computer/iroh) looks cool too.
Not sure whether I need the pub/sub things it offers yet, but speed is always nice!
