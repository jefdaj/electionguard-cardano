milestone 2
===========

This has been lots of experimenting with various dev tools so far,
and one working demo:

* [run elections + tests via mockchain + local IPFS](./mockchain-local-ipfs)

Investigate dev stacks
----------------------

Work in progress:

- [x] Aiken + Nix
- [ ] Aiken + Nix + MeshJS
- [ ] Aiken + Nix + PyCardano
- [x] Arion
- [x] Cardano Node + Docker
- [x] Cardano Node + Docker + Ogmios
- [x] Kupo + Docker
- [ ] IPFS + Docker
- [x] IPFS cluster + Docker
- [ ] Lucid + Kupmios
- [ ] MeshJS + Yaci
- [ ] Typescript + Nix
- [ ] [ThreadDB](https://docs.textile.io/threads/)

pubsub
------

I've been working on a small "pubsub" project to test the components I
think I want to use in the main ElectionGuard project:

1. [file syncing via IPFS](./pubsub1-ipfs)
2. [Aiken validator(s) + PyCardano](./pubsub2-aiken-pycardano)
