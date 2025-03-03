# pubsub1: IPFS sync with mock "blockchain" text file

This has two Python scripts in containers: publish.py and subscribe.py.
Each is networked with their own IPFS instance, and they share access to a text file `new_cids.txt`.
The publisher uploads files to IPFS and writes their CIDs to the file.
Subscribers monitor the file for CIDs to fetch and pin.

Syncing publisher -> subscribers works almost instantly on the local network,
and global access via `dweb.link` mostly works but takes a few seconds.
I assume the changes need to propagate, and the Dweb instances need to peer with mine or find a route to mine?


## TODO

- [ ] Pin IPFS container version.
- [ ] test syncing with publisher and subscriber in different physical locations.
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
