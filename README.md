<div align="center">

![](.github/electionguard-cardano-logo-v4.png)

ElectionGuard + Cardano
=======================
</div>

Work in progress on [the Catalyst fund13 project](https://milestones.projectcatalyst.io/projects/1300090).

Current status as of 2025-04-29:

- All Milestones (1, 2, and 3) approved

- [Milestone 1](./milestone1/) (ElectionGuard stuff):
  * The 3 main scripts basically work:
    - Output 1.1: [election](./milestone1/election)
    - Output 1.2: [verifier](./milestone1/verifier)
    - Output 1.3: [tests](./milestone1/tests)
  * In progress:
    - demo and explain everything
    - add failure/attack tests and fix any edge cases they reveal
  * Other misc things done along the way:
    - Have [electionguard-python passing its tests](./milestone1/electionguard-python-tests.md)
    - Cleaned up [my fork](https://github.com/jefdaj/electionguard-python)
      and pushed [a Docker image](https://ghcr.io/jefdaj/electionguard-python)
    - Partially archived [the NIST election format docs site](./milestone1/nist-docs)
    - Set up a [Nix environment](./milestone1/nix-environment.md)

- [Milestone 2](./milestone2/) (Cardano stuff):
  * [Cardano node + Ogmios](./milestone2/investigate/cardano-node-ogmios/) works
  * [Kupo](./milestone2/investigate/kupo/) works
  * [ipfs-cluster](./milestone2/investigate/ipfs-cluster/) works
  * [Aiken](./milestone2/investigate/aiken/) works
  * [PyCardano](./milestone2/investigate/aiken-pycardano) looks promising
  * Working on the [smart contract architecture](./milestone2/smart-contract-architecture.md)
  * Working on a small [pubsub dApp](./milestone2/pubsub) to test my ideas + dev stack

- [Milestone 3](./milestone3/) (ElectionGuard + Cardano integration):
  * Starting to plan demos
