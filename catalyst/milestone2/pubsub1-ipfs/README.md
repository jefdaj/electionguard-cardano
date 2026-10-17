# pubsub1: IPFS sync with mock "blockchain" text file

[demo]: ./asciinema-demo.mp4
[pubpy]: ./publisher/publish.py
[subpy]: ./subscriber/subscribe.py
[ac]: ./arion-compose.nix

[DEMO][demo]

There are two Python scripts: [publish.py][pubpy] and [subscribe.py][subpy].
In the demo there are two instances of the subscriber.
Each pub or sub script runs in a Docker container,
and each is networked to its own IPFS container.
Those IPFS containers are then networked together.
All the networking stuff happens in [arion-compose.nix][ac],
which generates + runs a Docker compose file.

The script containers also share access to a bind mounted text file `new_cids.txt`,
which stands in for the Cardano node + Aiken contract I'll be adding in the next section.

The publisher watches the publish dir for JSON files, wraps them with some info
about path and creation date, uploads them to IPFS, and writes their CIDs to
the file.

Subscribers monitor the file for CIDs to fetch and pin, read the JSON, and
reconstruct the published directory structure.

Syncing publisher -> subscribers works almost instantly on the local network,
and global access via `dweb.link` mostly works but takes a few seconds.  I
assume the changes need to propagate, and the Dweb instances need to peer with
mine or find a route to mine?


## TODO

- [x] Pin IPFS container version.
- [x] test syncing with publisher and subscriber in different physical locations.
- [ ] Is my top-level JSON `path` and `contents` format a rudimentary form of UnixFS?


## Usage

First, build and start the containers.
There should be one publisher (script + ipfs) and two subscribers (script + ipfs each).

```bash
./up.sh
# or
./up.sh offline
```

Now you should be able to add JSON files (along with parent dirs as needed) in
`/tmp/pubsub/pub1-publish` and see them propogate to
`/tmp/pubsub/sub{1,2}-subscribe`.

Note that you might have to `sudo` copy things into that folder, then `chmod`
them back to user permissions to get `publish.py` to pick them up.

You can also look at the latest CIDs in `/tmp/pubsub/new_cids/new_cids.txt`
and find them online at <https://dweb.link/ipfs/MYCID>.
Sometimes those will error out, but usually they show up immediately.


## Separate location tests

The obvious way does NOT seem to work:

- run two instances on different computers within the same (or different) LAN
- transfer `new_cids.txt` out of band from one to the other
- wait for the other's subscribers to pick up the files

Not sure why yet. Maybe I need to make sure I have connectivity to a popular relay node?
In any case it shouldn't be a problem in real elections, because 1) the admin can set up a nice cluster,
and 2) enough people will be interested in pinning the files to make it more reliable.
