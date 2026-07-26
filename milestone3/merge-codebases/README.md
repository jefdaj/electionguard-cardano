Merge codebases
===============

Things to merge:

- [ ] The M1 code runs test elections using a "mockchain", and verifies IPFS syncing.
      It runs on the older, now-outdated paradigm of electionguard-python containers.

- [ ] The M2 code runs test elections too but via a different codebase. It posts
      static artifacts (no ElectionGuard running) and doesn't do much with IPFS.

- [ ] Since M2, I've finally Nix packaged electionguard-python. So the integrated
      codebase can hopefully be just one `egc` Docker container built with Nix.

- [ ] I've also designed a client/server thing: that container will have a stateful
      FastAPI server + a Click CLI that talks to the server. Both demos and tests can
      use the CLI. Hopefully later, after the demo (post fund13 in general), I can
      elaborate the server with a webui and keep the CLI for the scripting/test
      cases.

Develop client/server code with env2
------------------------------------

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

Old tests
---------

These are working again and ready to be reorganized for a merged codebase:

```
$ nix develop
$ docker compose up -d
$ ./test.sh
============================= test session starts ==============================
platform linux -- Python 3.13.13, pytest-9.1.1, pluggy-1.6.0 -- /nix/store/w9qq9rlh5jks1ji7lm44q9w0z4fr1viw-electionguard-cardano/bin/python3.13
cachedir: .pytest_cache
rootdir: /home/jefdaj/myrepos/electionguard-cardano/milestone3/merge-codebases
configfile: pyproject.toml
testpaths: tests/setup, tests/unit, tests/integration, tests/demo
plugins: asyncio-1.4.0, anyio-4.14.1, typeguard-4.5.2, mock-3.15.1
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 70 items / 55 deselected / 15 selected

tests/unit/test_data.py::test_load_static_phases PASSED                  [  6%]
tests/unit/test_data.py::test_load_static_transactions PASSED            [ 13%]
tests/unit/test_data.py::test_load_static_record_pairs PASSED            [ 20%]
tests/unit/test_election.py::test_roundtrip_deployment PASSED            [ 26%]
tests/unit/test_election.py::test_roundtrip_electioncontext PASSED       [ 33%]
tests/unit/test_funder.py::test_funder_wallet PASSED                     [ 40%]
tests/unit/test_funder.py::test_pick_oneshot_utxo PASSED                 [ 46%]
tests/unit/test_funder.py::test_init_funder PASSED                       [ 53%]
tests/unit/test_records.py::test_roundtrip_static_records_to_str PASSED  [ 60%]
tests/unit/test_script.py::test_roundrip_oneshot_utxo PASSED             [ 66%]
tests/unit/test_script.py::test_parameterize_script PASSED               [ 73%]
tests/unit/test_script.py::test_roundtrip_script PASSED                  [ 80%]
tests/unit/test_wallets.py::test_admin_wallet PASSED                     [ 86%]
tests/unit/test_wallets.py::test_load_admin_wallet_by_address PASSED     [ 93%]
tests/unit/test_wallets.py::test_subchannel_wallets PASSED               [100%]

====================== 15 passed, 55 deselected in 1.20s =======================
============================= test session starts ==============================
platform linux -- Python 3.13.13, pytest-9.1.1, pluggy-1.6.0 -- /nix/store/w9qq9rlh5jks1ji7lm44q9w0z4fr1viw-electionguard-cardano/bin/python3.13
cachedir: .pytest_cache
rootdir: /home/jefdaj/myrepos/electionguard-cardano/milestone3/merge-codebases
configfile: pyproject.toml
testpaths: tests/setup, tests/unit, tests/integration, tests/demo
plugins: asyncio-1.4.0, anyio-4.14.1, typeguard-4.5.2, mock-3.15.1
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 70 items / 15 deselected / 55 selected

tests/setup/test_ogmios.py::test_ogmios_ready PASSED                     [  1%]
tests/setup/test_ogmios.py::test_query_network_tip PASSED                [  3%]
tests/unit/test_assets.py::test_admin_stt PASSED                         [  5%]
tests/unit/test_assets.py::test_subchannel_stts PASSED                   [  7%]
tests/unit/test_election.py::test_init_tx PASSED                         [  9%]
tests/unit/test_election.py::test_election_config PASSED                 [ 10%]
tests/unit/test_election.py::test_election_context PASSED                [ 12%]
tests/unit/test_nodes.py::test_init_admin PASSED                         [ 14%]
tests/unit/test_nodes.py::test_init_subchannel_nodes PASSED              [ 16%]
tests/unit/test_subscriber.py::test_init_subscriber PASSED               [ 18%]
tests/unit/test_subscriber.py::test_rollback PASSED                      [ 20%]
tests/unit/test_subscriber.py::test_admin_address PASSED                 [ 21%]
tests/integration/test_subchannels.py::test_tx0 PASSED                   [ 23%]
tests/integration/test_subchannels.py::test_tx1 PASSED                   [ 25%]
tests/integration/test_subchannels.py::test_add_subchannel PASSED        [ 27%]
tests/integration/test_subchannels.py::test_rm_subchannel PASSED         [ 29%]
tests/demo/test_happy_election.py::test_admin_tx0 PASSED                 [ 30%]
tests/demo/test_happy_election.py::test_phase0_announce PASSED           [ 32%]
tests/demo/test_happy_election.py::test_admin_tx1 PASSED                 [ 34%]
tests/demo/test_happy_election.py::test_admin_tx2 PASSED                 [ 36%]
tests/demo/test_happy_election.py::test_phase1_onboarding PASSED         [ 38%]
tests/demo/test_happy_election.py::test_guardian1_tx1 PASSED             [ 40%]
tests/demo/test_happy_election.py::test_guardian2_tx1 PASSED             [ 41%]
tests/demo/test_happy_election.py::test_guardian3_tx1 PASSED             [ 43%]
tests/demo/test_happy_election.py::test_phase2_ceremony_round1 PASSED    [ 45%]
tests/demo/test_happy_election.py::test_guardian1_tx2 PASSED             [ 47%]
tests/demo/test_happy_election.py::test_guardian2_tx2 PASSED             [ 49%]
tests/demo/test_happy_election.py::test_guardian3_tx2 PASSED             [ 50%]
tests/demo/test_happy_election.py::test_phase2_ceremony_round2 PASSED    [ 52%]
tests/demo/test_happy_election.py::test_guardian1_tx3 PASSED             [ 54%]
tests/demo/test_happy_election.py::test_guardian2_tx3 PASSED             [ 56%]
tests/demo/test_happy_election.py::test_guardian3_tx3 PASSED             [ 58%]
tests/demo/test_happy_election.py::test_device1_tx1 PASSED               [ 60%]
tests/demo/test_happy_election.py::test_admin_tx3 PASSED                 [ 61%]
tests/demo/test_happy_election.py::test_phase2_ceremony_round3 PASSED    [ 63%]
tests/demo/test_happy_election.py::test_device1_tx2 PASSED               [ 65%]
tests/demo/test_happy_election.py::test_device1_tx3 PASSED               [ 67%]
tests/demo/test_happy_election.py::test_admin_tx4 PASSED                 [ 69%]
tests/demo/test_happy_election.py::test_phase3_voting PASSED             [ 70%]
tests/demo/test_happy_election.py::test_admin_tx5 PASSED                 [ 72%]
tests/demo/test_happy_election.py::test_guardian1_tx4 PASSED             [ 74%]
tests/demo/test_happy_election.py::test_guardian2_tx4 PASSED             [ 76%]
tests/demo/test_happy_election.py::test_guardian3_tx4 PASSED             [ 78%]
tests/demo/test_happy_election.py::test_phase4_tally PASSED              [ 80%]
tests/demo/test_happy_election.py::test_admin_tx6 PASSED                 [ 81%]
tests/demo/test_happy_election.py::test_phase5_decrypt PASSED            [ 83%]
tests/demo/test_happy_election.py::test_guardian1_tx5 PASSED             [ 85%]
tests/demo/test_happy_election.py::test_guardian2_tx5 PASSED             [ 87%]
tests/demo/test_happy_election.py::test_guardian3_tx5 PASSED             [ 89%]
tests/demo/test_happy_election.py::test_verifier1_tx1 PASSED             [ 90%]
tests/demo/test_happy_election.py::test_admin_tx7 PASSED                 [ 92%]
tests/demo/test_happy_election.py::test_phase6_verify PASSED             [ 94%]
tests/demo/test_happy_election.py::test_admin_tx8 PASSED                 [ 96%]
tests/demo/test_happy_election.py::test_admin_tx9 PASSED                 [ 98%]
tests/demo/test_happy_election.py::test_phase7_finalize PASSED           [100%]

================ 55 passed, 15 deselected in 1109.52s (0:18:29) ================
```

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
