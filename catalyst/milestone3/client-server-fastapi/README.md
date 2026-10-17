ElectionGuard+Cardano Client/Server Sketch
==========================================

Server:

```
$ nix develop
$ egc server start
INFO:     Will watch for changes in these directories: ['.../electionguard-cardano/milestone3/client-server-fastapi']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [231266] using StatReload
INFO:     Started server process [231272]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

Client:

```
$ nix develop

$ egc server health
{'status': 'ok'}

$ egc election set \
    --policy-id a52bfeac6281fe3fa0f15a75159cefac25c0f41b2f742bd1efc32c74 \
    --slot-no 116668881 \
    --block-header-hash 567a2fbb6583f7bca0a5a5e6b24c9aa3509c040e079c6586aec16d2316e7ad41
201

$ egc election observe --filter guardian1 | tail -n3
ElectionEvent(id='electionevent-b790425f', tx_id='708e74f160adb368407aa9da8449a6a6a483f861a490de8230ad34a66ba6204f', slot_no=116669719, channel='guardian1', event_type='post record', event_desc="posted SpoiledShare(spoiled_id=b'ballot-4c9f842a-1d64-11f1-94d0-768fd7ed4145', guardian_number=1)")
ElectionEvent(id='electionevent-d59db6ab', tx_id='f369524541066d70a4925aeeaa74c1e4bc1514b9bd6c5a360ae9833eadd993b0', slot_no=116669813, channel='guardian1', event_type='post record', event_desc="posted Summary(verifier_id=b'guardian1')")
ElectionEvent(id='electionevent-6cee36fc', tx_id='d1e1159dfc0d1210eb37096e5138e446f943ed05630c68701811990e1e1ba615', slot_no=116670062, channel='admin', event_type='rm subchannel', event_desc='revoked guardian1 authorization')
```

Docker server:

```
$ nix build .#dockerImage
$ docker load < result
$ docker run -p 8000:8000 egc-client-server-sketch:0.1.1
INFO:     Will watch for changes in these directories: ['/']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [1] using StatReload
INFO:     Started server process [8]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```
