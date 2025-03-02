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

Ideally I can make this modular, so that only running one or multiple
entities/roles per computer uses the same code.

Seems the convention is Docker related networks start with `172`.

First attempt:

- subnets  : 172.{11,12,13,14}0.0/16
- gateways : 172.{11,12,13,14}0.1
- cardano  : 172.11.0.2
- ogmios   : 172.11.0.3
- ipfs     : 172.{12,13,14}.0.2
- pub/sub  : 172.{12,13,14}.0.3

TODO are there rules about the subnets not being a more obvious "1,2,3,..."?

Verdict: seems to work!
Can still access Ogmios on <http://172.13.0.3:1337>,
it can still connect to Cardano, and Cardano is still syncing.
Can also `curl http://example.com` from the Cardano container.
Publisher and subscriber both work too.

TODO is there a more elegant way to control firewall than by adding custom
`pubsub_lan` and `pubsub_wan` networks?
