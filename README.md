<div align="center">

![](.github/electionguard-cardano-logo-v2.png)

ElectionGuard + Cardano
=======================
</div>

Work in progress on [the Catalyst fund13 project](https://milestones.projectcatalyst.io/projects/1300090).

Current status as of 2024-03-01:

- All Milestones (1, 2, and 3) approved

- [Milestone 1](./milestone1/) (ElectionGuard stuff):
  * Have [electionguard-python passing its tests](./milestone1/electionguard-python-tests.md)
  * Cleaned up [my fork](https://github.com/jefdaj/electionguard-python)
    and pushed [a Docker image](https://ghcr.io/jefdaj/electionguard-python)
  * Partially archived [the NIST election format docs site](./milestone1/nist-docs)
  * The [Nix environment](./milestone1/nix-environment.md) works
  * The [local election script](./milestone1/local-election) (output 1.1) works
  * Next step is to demo + explain the local election script

- [Milestone 2](./milestone2/) (Cardano stuff):
  * [Cardano node + Ogmios](./milestone2/investigate/cardano-node-ogmios/) works
  * [Kupo](./milestone2/investigate/kupo/) works
  * [ipfs-cluster](./milestone2/investigate/ipfs-cluster/) works
  * [Aiken](./milestone2/investigate/aiken/) works
  * [PyCardano](./milestone2/investigate/aiken-pycardano) looks promising
  * Work in progress on the [smart contract architecture](./milestone2/smart-contract-architecture.md)

- [Milestone 3](./milestone3/) (ElectionGuard + Cardano integration):
  * Working on a small [pubsub dApp](./milestone3/pubsub) to test my ideas + dev stack
