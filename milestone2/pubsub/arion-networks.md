# arion networks

## Working but messy single network

```txt
subnet  = "172.32.0.0/16";
gateway = "172.32.0.1";

subscribers:
      subAddr  = "172.32.0.${toString (100 + portSuffix)}";
      ipfsHost = "172.32.0.${toString (150 + portSuffix)}";

publisher(s):
      pubAddr  = "172.32.0.${toString (100 + portSuffix)}";
      ipfsHost = "172.32.0.${toString (150 + portSuffix)}";
```

`docker network inspect pubsub` says that works out to:

  subnet 172.32.0.0/16
  gateway 172.32.0.1

  pubsub-pub1-publish-1   172.32.0.101/16
  pubsub-pub1-ipfs-1      172.32.0.151/16

  pubsub-sub1-subscribe-1 172.32.0.102/16
  pubsub-sub1-ipfs-1      172.32.0.152/16

  pubsub-sub2-subscribe-1 172.32.0.103/16
  pubsub-sub2-ipfs-1      172.32.0.153/16


## Single role per computer (for later)

I think using the "host" network, every container will just be at the host's actual IP?
As long as they're only running containers for one role and don't re-use ports,
that should be perfect.


## Separate network per entity


