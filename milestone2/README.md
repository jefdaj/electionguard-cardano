# milestone 2

So far this has been a lot of research into the Cardano ecosystem
and trying various partial dev stacks.

I'm still doing that, but also starting a small [pubsub/]() project to test the
components I think I want to use in the main ElectionGuard project.


## Investigate partial dev stacks

These are works in progress under [investigate/]():

- [x] Aiken + Nix
- [ ] Aiken + Nix + MeshJS
- [ ] Aiken + Nix + PyCardano
- [ ] Arion
- [x] Cardano Node + Docker
- [x] Cardano Node + Docker + Ogmios
- [x] Kupo + Docker
- [ ] IPFS + Docker
- [x] IPFS cluster + Docker
- [ ] Lucid + Kupmios
- [ ] MeshJS + Yaci
- [ ] Typescript + Nix


## Smart Contract Architecture

Just some initial ideas.

Main data:
- election state NFT
- admin, guardian, mediator NFTs
- election metadata (in the NFT?)
- election record Merkle Patricia Tree root
- message queue
- general funds for TX fees

The message queue is for incoming signed ballots, and other messages like final election verifications/disputes.
In the future it could also have Benaloh challenge certifications/disputes by voters.

The general fund could expand later into a map holding collateral from various parties.

See `electionguard_gui/models/key_ceremony_states.py` for a state machine starting point.

TODO can the plutus contract do all verification of incoming data itself, then force batchers to include every TX? Or will there eventually need to be a dispute resolution mechanism for that?
