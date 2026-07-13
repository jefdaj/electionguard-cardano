Merge M1 + M2 code
==================

The M1 code runs test elections using a "mockchain", and verifies IPFS syncing.
It runs on the older, now-outdated paradigm of electionguard-python containers.

The M2 code runs test elections too but via a different codebase. It posts
static artifacts (no ElectionGuard running) and doesn't do much with IPFS.

Since M2, I've finally Nix packaged electionguard-python. So the integrated
codebase can hopefully be just one `egc` Docker container built with Nix.
