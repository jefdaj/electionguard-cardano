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

I think the best way to start getting a grip on the code is to visualize the on-chain data structure. It's basically a multithreaded pubsub channel:

