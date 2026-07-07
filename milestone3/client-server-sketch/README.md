ElectionGuard+Cardano Client/Server Sketch
==========================================

```
$ nix develop

$ egc-server 
hello from egc-server

$ egc
hello from egc (client)
```

```
$ nix build .#dockerImage
$ docker load < result
$ docker run egc-client-server-sketch:0.1.0
hello from egc-server

```
