<div align="center">

![](.github/electionguard-cardano-logo-v2.png)

ElectionGuard + Cardano
=======================
</div>

Work in progress on [the Catalyst fund13 project](https://milestones.projectcatalyst.io/projects/1300090).

Current status as of 2025-03-16:

- All Milestones (1, 2, and 3) approved

- [Milestone 1](./milestone1/) (ElectionGuard stuff):
  * Have [electionguard-python passing its tests](./milestone1/electionguard-python-tests.md)
  * Cleaned up [my fork](https://github.com/jefdaj/electionguard-python)
    and pushed [a Docker image](https://ghcr.io/jefdaj/electionguard-python)
  * Partially archived [the NIST election format docs site](./milestone1/nist-docs)
  * The [Nix environment](./milestone1/nix-environment.md) works
  * The [election script](./milestone1/election) (output 1.1) works
  * The [verifier script](./milestone1/verifier) (output 1.2) works
  * Working on the [test script](./milestone1/tests) (output 1.3)
  * Next steps are:
    - demo + explain the election and verifier scripts
    - fix whatever edge cases the tests uncover in the election and verifier scripts

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
