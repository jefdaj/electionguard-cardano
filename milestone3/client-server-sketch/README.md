ElectionGuard+Cardano Client/Server Sketch
==========================================

Server:

```
$ nix develop
$ egc serve
 * Serving Quart app 'egc_app.server.app'
 * Debug mode: False
 * Please use an ASGI server (e.g. Hypercorn) directly in production
 * Running on http://0.0.0.0:5000 (CTRL + C to quit)
[2026-07-07 21:41:30 -0700] [3250111] [INFO] Running on http://0.0.0.0:5000 (CTRL + C to quit)
```

Client:

```
$ nix develop

$ egc health
{'status': 'ok'}

$ egc state
{'state': 0}

$ egc incr 3
$ egc incr 2

$ egc state
{'state': 5}

$ egc subscribe \
    --policy-id a52bfeac6281fe3fa0f15a75159cefac25c0f41b2f742bd1efc32c74 \
    --slot-no 116668881 \
    --block-header-hash 567a2fbb6583f7bca0a5a5e6b24c9aa3509c040e079c6586aec16d2316e7ad41
```

Docker server:

```
$ nix build .#dockerImage
$ docker load < result
$ docker run -p 5000:5000 egc-client-server-sketch:0.1.0 serve
```
