<div align="center">

![](.github/electionguard-cardano-logo-v4.png)

ElectionGuard + Cardano
=======================
</div>

[yt]: https://youtube.com/@prosocialcrypto
[blog]: https://cryptoisland.blog/tags/electionguard.html

Work in progress on [the Catalyst fund13 project](https://milestones.projectcatalyst.io/projects/1300090).

Current status as of 2026-07-03:

- All Milestones (1, 2, and 3) approved

- [x] [Milestone 1](./milestone1/) (ElectionGuard stuff) finished:
  * The 3 main scripts work:
    - [x] Output 1.1: [election](./milestone1/election)
    - [x] Output 1.2: [verifier](./milestone1/verifier)
    - [x] Output 1.3: [tests](./milestone1/tests)
  * They each have a companion video on [my YouTube channel][yt] and post on [my blog][blog]
  * Other misc things done along the way:
    - Have [electionguard-python passing its tests](./milestone1/electionguard-python-tests.md)
    - Cleaned up [my fork](https://github.com/jefdaj/electionguard-python)
      and pushed [a Docker image](https://ghcr.io/jefdaj/electionguard-python)
    - Partially archived [the NIST election format docs site](./milestone1/nist-docs)
    - Set up a [Nix environment](./milestone1/nix-environment.md)

- [x] [Milestone 2](./milestone2/) (Cardano stuff) finished:

  * [x] Output 2.1  [design docs](./milestone2/publish-and-verify/onchain/)
  * [x] Output 2.2: [publish script](./milestone2/publish-and-verify/offchain/publish.py)
  * [x] Output 2.3: [verify script](./milestone2/publish-and-verify/offchain/verify.py)
  * Outputs 2 and 3 have combined YouTube videos (2 videos, both about both) + one combined blog post.
  * Other misc things done along the way:
    - [An IPFS-ified version of the 1.1 tests codebase](./milestone2/mockchain-local-ipfs) works
    - [I worked a bit on making it more efficient](./milestone2/mockchain-local-ipfs-parallel)
    - A minimal "pubsub" example shows that the plan for the election dApp is viable:
      * [mockchain version with IPFS only](./milestone2/pubsub1-ipfs) syncs files given CIDs
      * [Aiken + PyCardano + Kupo version](./milestone2/pubsub2-aiken-pycardano-kupo) syncs CIDs via Preview testnet

- [ ] [Milestone 3](./milestone3/) (ElectionGuard + Cardano integration):

  * Figured out overall architecture: Docker images, APIs, etc.
  * Started experimenting with [printing and scanning QR codes](./milestone3/qrcodes)
  * Starting to plan demos + talk
