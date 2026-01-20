<div align="center">

![](.github/electionguard-cardano-logo-v4.png)

ElectionGuard + Cardano
=======================
</div>

[yt]: https://youtube.com/@prosocialcrypto
[blog]: https://cryptoisland.blog/tags/electionguard.html

Work in progress on [the Catalyst fund13 project](https://milestones.projectcatalyst.io/projects/1300090).

Current status as of 2026-01-20:

- All Milestones (1, 2, and 3) approved

- [Milestone 1](./milestone1/) (ElectionGuard stuff) finished:
  * The 3 main scripts work:
    - Output 1.1: [election](./milestone1/election)
    - Output 1.2: [verifier](./milestone1/verifier)
    - Output 1.3: [tests](./milestone1/tests)
  * They each have a companion video on [my YouTube channel][yt] and post on [my blog][blog]
  * Other misc things done along the way:
    - Have [electionguard-python passing its tests](./milestone1/electionguard-python-tests.md)
    - Cleaned up [my fork](https://github.com/jefdaj/electionguard-python)
      and pushed [a Docker image](https://ghcr.io/jefdaj/electionguard-python)
    - Partially archived [the NIST election format docs site](./milestone1/nist-docs)
    - Set up a [Nix environment](./milestone1/nix-environment.md)

- [Milestone 2](./milestone2/) (Cardano stuff) in progress:

  * [An IPFS-ified version of the 1.1 tests codebase](./milestone2/mockchain-local-ipfs) works

  * A minimal "pubsub" example shows that the plan for the election dApp is viable:
    - [mockchain version with IPFS only](./milestone2/pubsub1-ipfs) syncs files given CIDs
    - [Aiken + PyCardano + Kupo version](./milestone2/pubsub2-aiken-pycardano-kupo) syncs CIDs via Preview testnet

  * Working on the [smart contract architecture](./milestone2/smart-contract-architecture.md)

- [Milestone 3](./milestone3/) (ElectionGuard + Cardano integration):

  * Starting to plan demos

  * Started experimenting with [printing and scanning QR codes](./milestone3/qrcodes)
