# Tour of the electionguard-cardano validator code

In this first MVP version of the ElectionGuard + Cardano system, the on-chain code serves two purposes, both related to limiting the power of the government (AKA election administrator) by decentralizing some of their duties:

1. The contract acts as the "public, append-only bulletin board". In traditional non-blockchain ElectionGuard deployments, this would just be website. Decentralizing it removes the temptation for the admin to alter records or take the site down if they don't like how the election is going, and reduces their exposure to being hacked or DDoSed.

2. The contract also makes it easier for the head administrator to delegate authority. Instead of one monolithic "election system" the public can see the admin assigning other keys to particular roles (guardian, ballot encryption device, official verifier) and knows which one(s) signed each election artifact.

There are many other things the blockchain would also be useful for, but they're left for future versions:

- uncensorable disputes and transparent dispute resolution
- provably random (unbiased) risk-limiting audits
- collateral/slashing to improve trust in election officials
- incentives for 3rd parties to host and serve data
- ...

## Visualizing the on-chain data

Cardano smart contracts can be tricky to visualize because they don't construct transactions; they only decide whether a given transaction made by off-chain code is valid or not. I think the simplest place to start is with an example of the data structure they're trying to force the offchain code to create.

In this case it's a multithreaded pubsub channel, like this:

