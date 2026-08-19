Merge codebases
===============

I have a bunch of different bits of code working individually, and the current
work is focused on integrating them all. The merged code will be used for all the
M3 deliverables, and hopefully become the one main codebase from now on.

Current status as of 2026-08-19:

- [x] Operate existing egc code (nodes etc) from egc server
- [x] Nix-built Docker image that auto-runs the egc server
- [x] Unified Nix build with electionguard-python, egc, Plutus blueprints, client/server app, Docker image
- [x] QRCodes: scan from webcam, print to terminal, save/load as txt or png
- [x] All election officials can optionally announce IPFS peer_id + addr_hints on chain
- [x] IPFS peering with any on chain peer, and auto-discovery of how to dial it (may need real life tuning)
- [x] Auto fetch PublicRecords and save them to a local public records dir
- [x] New test harness for client/server app using generated bash scripts
- [x] Get all tests passing together in one pytest suite
- [x] Generate random manifests with "office" or "referendum" contests
- [x] CLI create, load, save, show wallets
- [x] CLI election operations: create, subscribe, burntesttokens, stream events
- [x] CLI post public records
- [x] CLI batch interface: create various artifacts, post them together with `egc records post`
- [x] CLI ipfs operations: show, post
- [x] CLI channel operations: request (generate qrcode), add (accept qrcode requests), await
- [x] CLI phase operations: show, await, advance
- [ ] CLI key ceremony operations
- [ ] CLI device operations
- [ ] CLI tally operations
- [ ] CLI verify operations
- [ ] demo scripts (outputs 3.1, 3.2)
- [ ] multi-computer testing (outout 3.3)
- [ ] give a demo + talk (output 3.4)

Things being merged:

- The M1 code runs test elections using a "mockchain", and verifies IPFS syncing.
  It runs on the older, now-outdated paradigm of electionguard-python containers.

- The M2 code runs test elections too but via a different codebase. It posts
  static artifacts (no ElectionGuard running) and doesn't do much with IPFS.

- Since M2, I've finally Nix packaged electionguard-python. So the integrated
  codebase can hopefully be just one `egc` Docker container built with Nix.

- I've also designed a client/server thing: that container will have a stateful
  FastAPI server + a Click CLI that talks to the server. Both demos and tests can
  use the CLI. Hopefully later, after the demo (post fund13 in general), I can
  elaborate the server with a webui and keep the CLI for the scripting/test
  cases.

- I separately mocked up an idea for the voter authorization workflow using
  QRcodes and ED25519 keys.

Tests
-----

These are being updated/written as I go. They should hopefully always be passing on the trunk branch.

```
$ nix develop
$ ./test.sh
```

Dev
---

Develop client/server code with env2

```
# terminal 1
$ nix develop
$ python src/egc_app/cli/__init__.py node run --private-dir /tmp/whatever/
```

```
# terminal 2
$ nix develop
$ python src/egc_app/cli/__init__.py <cli args>
```

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

Run EGC scripts:

```
$ docker exec -it election-verifier1-egc-1 bash /scripts/verifier.sh
node is ready
```

Monitor the network:

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
