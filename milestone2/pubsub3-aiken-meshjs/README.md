pubsub dApp test #3: ipfs, aiken, meshjs
========================================

An alternate version of [pubsub2-aiken-pycardano](../pubsub2-aiken-pycardano)
using meshjs instead for comparison, because I ran into some problems with
pycardano. The expected tradeoff in this version is that TX building will be
easier, but there will be some extra complexity later related to writing part
of the code in JS and part of it in Python.

Dev
---

```
nix develop
npm run build
npm start
npm run dev
# etc
```

```
nix develop .#onchain
aiken check
aiken build
# etc
```

```
nix build
./result/bin/pubsub
```


TODO
----

- [x] simpler setup where publisher and subscriber are the same script?
- [x] add JS to Nix files
- [ ] rewrite generate-keys in JS and create a new keypair
- [ ] follow the rest of the Aiken hello world tutorial using Mesh
- [ ] translate test.py to JS
- [ ] translate publish.py to JS
