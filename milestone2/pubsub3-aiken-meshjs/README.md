# pubsub3: post CIDs to preview testnet using ipfs, aiken, meshjs (instead of pycardano)

An alternate version of [pubsub2-aiken-pycardano](../pubsub2-aiken-pycardano)
using meshjs instead for comparison, because I ran into some weird transaction
construction issues with pycardano. The expected tradeoff in this version is
that TX building will be easier, but there will be some extra complexity
related to writing part of the code in JS.

TODO:

- [ ] add JS to Nix files
- [ ] rewrite generate-keys in JS and create a new keypair
- [ ] follow the rest of the Aiken hello world tutorial using Mesh
- [ ] translate test.py to JS
- [ ] translate publish.py to JS
