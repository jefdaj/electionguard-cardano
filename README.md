<div align="center">

![](.github/electionguard-cardano-logo-v4.png)

ElectionGuard + Cardano
=======================
</div>

[yt]: https://youtube.com/@prosocialcrypto
[blog]: https://cryptoisland.blog/tags/electionguard.html

Work in progress on [the Catalyst fund13 project](https://milestones.projectcatalyst.io/projects/1300090).

Current status as of 2026-07-18:

- [ ] [Milestone 3](./milestone3/) (ElectionGuard + Cardano integration):

  * Currently working on [merging the M1 + M2 + M3 codebases](./milestone3/merge-codebases)
  * [Designed the auth token workflow and polling place stations](./milestone3/tokens-and-stations)
  * [Designed the CLI](./milestone3/cli-design)
  * [Nix Packaged the reference implementation](https://github.com/jefdaj/electionguard-python) (finally!)
  * [M1 mockchain tests using new Nix Docker](./milestone3/egpy-upgrade-nix-docker)
  * Experimented with [a Quart + HTMX WebUI](./milestone3/webui-quart-htmx)
  * Experimented with [printing and scanning QR codes](./milestone3/qrcodes)
  * Starting to plan demos + talk

- [x] [Milestone 2](./milestone2/) (Cardano stuff) finished:

  * [x] Output 2.1  [design docs](./milestone2/design/) and [video](https://www.youtube.com/watch?v=zWpfJSx9b1I)
  * [x] Output 2.2: [publish script](./milestone2/publish-and-verify/offchain/publish.sh)
  * [x] Output 2.3: [verify script](./milestone2/publish-and-verify/offchain/verify.sh)
  * Outputs 2 and 3 have combined YouTube videos (2 videos, [both](https://www.youtube.com/watch?v=Dr2lltC-zw0) about [both](https://www.youtube.com/watch?v=Qe0vyI1Zazo)) + one combined [blog post](https://cryptoisland.blog/posts/2026/07/03/egc-dev07-publish-and-verify/) and [Asciinema demo](https://asciinema.org/a/1260144).
  * Other misc things done along the way:
    - [An IPFS-ified version of the 1.1 tests codebase](./milestone2/mockchain-local-ipfs) works
    - [I worked a bit on making it more efficient](./milestone2/mockchain-local-ipfs-parallel)
    - A minimal "pubsub" example shows that the plan for the election dApp is viable:
      * [mockchain version with IPFS only](./milestone2/pubsub1-ipfs) syncs files given CIDs
      * [Aiken + PyCardano + Kupo version](./milestone2/pubsub2-aiken-pycardano-kupo) syncs CIDs via Preview testnet

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
