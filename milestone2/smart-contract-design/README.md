smart contract design
=====================

This is the draft smart contract design based on merging two previous experiments:

* [pubsub2-aiken-pycardano-kupo](../pubsub2-aiken-pycardano-kupo), which publishes simple lists of CIDs to the Preview testnet

* [mockchain-local-ipfs](../mockchain-local-ipfs), which mocks up a more complete multi threaded election protocol locally using JSON files

This design will be a complete working election protocol to the best of my knowledge,
but actually implementing and testing it is left for milestone 3.
And at that point, I might discover some things that need to be changed!
If so, I'll keep this doc updated and start a CHANGELOG.

General Idea
------------

The contract is a multi-threaded pubsub channel where the admin can create sub-channels and authorize + pay for other wallets to post to them.
All other actors in the election (guardians, voting machines, verifiers) post events to their particular sub-channel.
An event is either a public election artifact (and IPFS CID + metadata) or a channel-related action: open, fork, close.

Anyone can also run the same egsync client election actors do to subscribe to messages, download the IPFS files, and confirm whether everything is being done according to the protocol or not. They just can't post messages without being authorized.

Future directions
-----------------

Things that aren't part of the current design but I'd like to add at some point:

* Some channels should be open for the public to post disputes or verifications (perhaps with collateral requirements to prevent spam?).

* There are various checks that could be built into the smart contract, but there will still be some parts that have to be validated separately (for example JSON schemas of the files corresponding to the CIDs).
AFAIK that requirement can't be removed until we get to the point of the whole thing being zero knowledge provable.
