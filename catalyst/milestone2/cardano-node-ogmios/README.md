# Cardano node + ogmios

I've been running this separately from the other infrastructure for each of my
test codebases so I only have to keep one copy of the node data. Here's how to
start it.

```bash
$ nix develop
$ docker compose up -d
$ docker compose logs --follow
```
