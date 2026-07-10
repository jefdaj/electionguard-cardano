CLI Design
==========

The [client/server sketch with Click/FastAPI](../client-server-fastapi) seems good.
Now I'm fleshing out the CLI commands and workflows. Assuming that goes well,
the next step will be to write a version of the election + test scripts that runs
a bash script of `egc` commands per node rather than `docker exec`ing each command
individually.

While designing the commands, I'm also running into a few edge cases I hadn't
thought of before and fixing them...


Overview
--------

```
config       : node, election, batch, ... (maybe more)
server       : start, status, stop
election     : init, observe, end, burntesttokens
channel      : request, add, remove, await
ballot       : create, submit (both batch and save token), lookup (by token), cast, spoil
manifest     : create, announce
phase        : announce, await
ceremony     : create, announce, keygen, announce-key, backup, confirm-backups
tally        : create, announce, announce-share, combine-shares
spoiled      : announce-share, combine-shares, decrypt-by-nonce (later)
verification : create, announce, await
batch        : add, status, flush
```


Config
------

I'm thinking a main JSON config file, and you can override parts of it at
runtime, and then optionally re-save that as a file.


Challenge Workflow
------------------

I think an explicit mapping of ballot ID -> random token/UUID saved as files in
a dedicated private dir makes the most sense for now. That could later be
adapted to separate the submit and challenge (cast/spoil) stations into
separate nodes if needed. And in the meantime it will be easy to debug.

The random token will be shown to the voter as a QR code and also saved to
disk. Then the voter goes over to the challenge station and stands in another
line, and at the same time hopefully the submit goes through on chain. Then at
the challenge station they present the token as proof they're the same voter,
and get to cast/spoil.

There should also be an initial "eligible voter" token given by whoever checks
voter registrations to get into the submit line. In a real election, a new one
of these would be issued by the challenge station when spoiling so you can go
around again. But for the demo version I think relying on physical security +
an audible "ding" or similar is reasonable.


QR Codes
--------

They're just a transport, and could carry many things. Those could be JSON, or
custom text. I'll start with custom text using `to/from_qrcode` class methods
on the dataclasses. Containers can have `qrcodes_in/out` bind mounts to
simulate scanning and showing them. For the first version there will be:

- challenge tokens
- final voter reciepts (for checking your ballot was included later)
- channel requests with node `VerificationKeyHash`es for the admin to authorize

Future versions might also have a mechanism for election officials to do
airgapped transactions. I'm not sure yet whether the security gain would
outweigh the UX complexity in most cases.


Batching
--------

In the demo, batching will be pretty simple with a min and max number of
records. In future versions it can be elaborated to guarantee a minimum
anonymity set for voters (a bunch of complexity hides there!), and to calculate
the actual number of records that will fit in a transaction.

This also brings up an issue with phase advancing: we need a grace period
between when the phase is announced on chain and when it takes effect, to
give everyone time to flush their batches. That will be added to the Aiken
contract.

```
egc batch add     ...   # (internal: what create/submit call)
egc batch status        # show pending count, oldest age, whether flushable
egc batch flush [--force] [--max N] [--min M]
```

```
Trigger	Rule
max size	pending ≥ max → flush immediately (a full tx)
timer	oldest record age ≥ flush_interval and pending ≥ min
manual	batch flush → flush if ≥ min, else refuse (unless --force)
phase end	if the phase advances, force-flush remaining during grace period
```

It might also be nice to have a verification alias that verifies all records in
the current batch.

I think the pending records added to the current batch can just go in a private
state dir for now. In fact they could go there by default with no need for an
explicit --out-json path when creating them.
