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

Set up a test network:

```
nix develop
nix build .#dockerImage
docker load < result
export ELECTION_JSON=$PWD/election.json
arion up -d
```

Monitor it:

```
arion logs -f
./watch-docker.sh
```

Test changes to electionguard-python:

```
nix develop --override-input electionguard-python path:$HOME/myrepos/electionguard-python
```

Be careful not to update pyproject.toml or uv.lock to include the temporary version.
