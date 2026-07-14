Merge codebases
===============

The M1 code runs test elections using a "mockchain", and verifies IPFS syncing.
It runs on the older, now-outdated paradigm of electionguard-python containers.

The M2 code runs test elections too but via a different codebase. It posts
static artifacts (no ElectionGuard running) and doesn't do much with IPFS.

Since M2, I've finally Nix packaged electionguard-python. So the integrated
codebase can hopefully be just one `egc` Docker container built with Nix.

I've also designed a client/server thing: that container will have a stateful
FastAPI server + a Click CLI that talks to the server. Both demos and tests can
use the CLI. Hopefully later, after the demo (post fund13 in general), I can
elaborate the server with a webui and keep the CLI for the scripting/test
cases.

Dev
---

You can pull in local work on electionguard-python, but it's a little iffy
because you have to be careful of uv commands that might try to update
pyproject.toml or uv.lock and get messed up by the temporary version. I haven't
found a better way yet...

```
nix develop --override-input electionguard-python path:$HOME/myrepos/electionguard-python
```
