# Smart Contract Architecture

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
