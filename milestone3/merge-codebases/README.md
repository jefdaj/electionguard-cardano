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
arion logs -f

# when done
arion down
```

Monitor it:

```
$ ./watch-docker.sh
networks:
7272320865e0   bridge                          bridge    local
04d385137391   election_admin-ipfs-net         bridge    local
21c8ba0538c1   election_admin-ogmios-net       bridge    local
8de80a3e4aac   election_cardano-net            bridge    local
321462576d17   election_device1-ipfs-net       bridge    local
a1f76aca112e   election_device1-ogmios-net     bridge    local
9715721f850f   election_guardian1-ipfs-net     bridge    local
c68f4fa8cabb   election_guardian1-ogmios-net   bridge    local
fbc93bb28183   election_guardian2-ipfs-net     bridge    local
5dde9766863d   election_guardian2-ogmios-net   bridge    local
f8b71a8c482a   election_guardian3-ipfs-net     bridge    local
f51b1e1c6768   election_guardian3-ogmios-net   bridge    local
66997aedf031   election_ipfs-mesh-net          bridge    local
ad57788ecd6c   election_verifier1-ipfs-net     bridge    local
c5e1af32b749   election_verifier1-ogmios-net   bridge    local
ba92ed021251   host                            host      local
ec702decfa44   none                            null      local

containers:
election-admin-egc-1        0.29%     101.4MiB / 62.64GiB
election-admin-ipfs-1       0.47%     49.91MiB / 62.64GiB
election-device1-egc-1      0.31%     101.4MiB / 62.64GiB
election-device1-ipfs-1     3.05%     59.07MiB / 62.64GiB
election-guardian1-egc-1    0.28%     105.4MiB / 62.64GiB
election-guardian1-ipfs-1   3.14%     51.64MiB / 62.64GiB
election-guardian2-egc-1    0.30%     101.4MiB / 62.64GiB
election-guardian2-ipfs-1   0.59%     55.34MiB / 62.64GiB
election-guardian3-egc-1    0.26%     101.6MiB / 62.64GiB
election-guardian3-ipfs-1   2.40%     55.43MiB / 62.64GiB
election-shared-cardano-1   0.68%     3.429GiB / 62.64GiB
election-shared-ogmios-1    0.00%     22.99MiB / 62.64GiB
election-verifier1-egc-1    0.30%     101.4MiB / 62.64GiB
election-verifier1-ipfs-1   2.66%     60.91MiB / 62.64GiB
```

Test changes to electionguard-python:

```
nix develop --override-input electionguard-python path:$HOME/myrepos/electionguard-python
```

Be careful not to update pyproject.toml or uv.lock to include the temporary version.
