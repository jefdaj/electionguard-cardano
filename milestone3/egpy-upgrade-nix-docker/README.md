Upgrade egpy container to py313-nix
===================================

Part of merging the M1 + M2 codebases.

This is an update of the [M2 mockchain parallel tests codebase](../../milestone2/mockchain-local-ipfs-parallel)
to use my new Nix based Docker image. It also adds a few misc niceties along the way:

- better watch scripts
- non-root data permissions (works for new egpy containers, but not old egsync ones)
