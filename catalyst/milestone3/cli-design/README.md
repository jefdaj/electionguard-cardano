CLI Design
==========

The [client/server sketch with Click/FastAPI](../client-server-fastapi) seems good.
Now I'm fleshing out the CLI commands and workflows. Assuming that goes well,
the next step will be to write a version of the election + test scripts that runs
a bash script of `egc` commands per node rather than `docker exec`ing each command
individually.

While designing the commands, I'm also running into a few edge cases and fixing them.


Overview
--------

```
config       : node, election, batch, ... (maybe more)
server       : start, status, stop
election     : init, observe, end, burntesttokens
channel      : request, add, remove, await
ballot       : create, submit (add to batch + save token), cast or spoil (by token)
manifest     : create, announce
phase        : announce, await
ceremony     : create, announce, keygen, announce-key, announce-backup, confirm-backup
tally        : create, announce, announce-share, combine-shares
spoiled      : announce-share, combine-shares, decrypt-by-nonce (future work)
verification : create, announce, await
batch        : add, status, flush
```


Roles
-----

Because there are a lot of commands, I added a way to filter them by role.
For example here are all the key ceremony commands:

```
$ egc ceremony
Usage: egc ceremony [OPTIONS] COMMAND [ARGS]...

  Perform the guardian key ceremony.

Options:
  --help  Show this message and exit.

All commands:
  announce
  announce-backup
  announce-pubkey
  confirm-backup
  create
  keygen
```

And here are the ones an admin, guardian, and verifier can do respectively:

```
$ egc --role admin ceremony
Usage: egc ceremony [OPTIONS] COMMAND [ARGS]...

  Perform the guardian key ceremony.

Options:
  --help  Show this message and exit.

Admin commands:
  announce
  create

$ egc --role guardian ceremony
Usage: egc ceremony [OPTIONS] COMMAND [ARGS]...

  Perform the guardian key ceremony.

Options:
  --help  Show this message and exit.

Guardian commands:
  announce-backup
  announce-pubkey
  confirm-backup
  keygen

$ egc --role verifier ceremony
Usage: egc ceremony [OPTIONS] COMMAND [ARGS]...

  Perform the guardian key ceremony.

Options:
  --help  Show this message and exit.

No verifier commands in this group.
```


Config
------

There's an optional JSON config file, and you can override parts of it at
runtime. You can also set options with environment variables.
Here two required args are picked up from the config and one from the env:

```json
{
	"election": {
		"subscribe": {
			"since_slot": 117083322,
			"since_block": "a8a5153fc6532593c67b5e7672a7cad64d7073bacb0bdf53e21dd8ae3bada95a"
		}
	}
}
```

```
$ export EGC_ELECTION_SUBSCRIBE_POLICY_ID=af3dc31662117bc7e821eb2e29271138d23a9e2688149b306de25fa8
$ egc --config config.json election subscribe
201
```

You can also save the live node config back to JSON.
Notice that `--config` isn't used here; the defaults come from earlier
`egc node run` and `egc election subscribe` commands:

```
$ egc config save config2.json
Saved config → config2.json
```

```json
{
  "election": {
    "subscribe": {
      "policy_id": "af3dc31662117bc7e821eb2e29271138d23a9e2688149b306de25fa8"
      "since_slot": 117083322,
      "since_block": "a8a5153fc6532593c67b5e7672a7cad64d7073bacb0bdf53e21dd8ae3bada95a",
    }
  }
  "node": {
    "host": "0.0.0.0",
    "port": 8000,
    "dev_mode": true
  }
}
```


Challenge Workflow
------------------

I think an explicit mapping of random token (UUID?) -> ballot saved as files in
a dedicated private dir makes the most sense for now. That could later be
adapted to separate the submit and challenge (cast/spoil) stations into
separate nodes if needed. And in the meantime it will be easy to debug.

There should be an initial "vote in progress token" given by whoever checks
voter registrations. That's needed to submit a ballot at the submit station,
and then also at the challenge station to cast/spoil it.

TODO should these be two different random tokens? Or is one OK?

In the case of a spoil, the challenge station issues a new vote in progress
token, unlinked to the previous one, and the voter can loop back around.


QR Codes
--------

I'll start with custom text using `to/from_qrcode` class methods
on the dataclasses. Containers can have `qrcodes_in/out` bind mounts to
simulate scanning and showing them. For the first version there will be:

- vote in progress tokens
- final voter receipts (for checking your ballot was included later)
- channel requests with node `VerificationKeyHash`es for the admin to authorize

Future versions might also have a mechanism for election officials to do
airgapped transactions. I'm not sure yet whether the security gain would
outweigh the UX complexity in most cases.

First working round-trip is the SubscriberConfig.
Note this looks nice in a terminal; it's only messed up on Github:

```
$ egc election qrcode
                                                         
                                                         
    █▀▀▀▀▀█  ▄▀█▄▄▄ ▀█▄▄██▀█ ▄█▄▄██▄ █▀  ▄▄▄█ █▀▀▀▀▀█    
    █ ███ █  ▀▀ ▄▀█▄▄ ▄▀▀▄▄▄▀ ▀█ ▄██▀ ▀▄   █▀ █ ███ █    
    █ ▀▀▀ █ ▄▀▄▀ █▄█▄ █▀█▄█▀▀▀█▄ ▄█▀█ ▄▄ ▄▄   █ ▀▀▀ █    
    ▀▀▀▀▀▀▀ ▀▄▀ █▄█▄█▄█ ▀ █ ▀ █▄▀▄▀▄█ █▄█▄▀▄▀ ▀▀▀▀▀▀▀    
    ▀▄ ▀▄█▀▄██▄ █▀▀▄▀▀▀█▀█▀▀▀▀▀█▀▄   ▄ ▄█▄ █ █ ▀ ▄▄ ▄    
    ▀▄ █ ▀▀█▄▀█▄  ▀▀█▀ ██▄▀ █▀▄ ▄█ ▄▀▀▀ █▄▄▀ █▄▀ █ ▄▀    
    ▀ ██ █▀▄▄▄▄▄▄▀▀█▀ ▄▄█▀ ▀█  ▄▀▀▀▀▀▀█▀▀▀  ▄ ▀▄▀▀▄██    
    ▄█▄█▀▄▀▀█▄ ▄█▀█ ▀▀▄ █ ▄▀██▀▄██ ▄█▄ ▀▄█▀▀ ▀ ▄▄▀▀ ▀    
     █▄█ █▀██▄  █ █ █  ▄▄▄ ▄▀▀▄█▄▀▀▄▀▄▀▄█▄▄ ▀ ▀ █ ▀▀█    
    ▀▀█▄▀ ▀ █▄█ ▀█▄▀▀█▄█ ██▄█   ▀▀ ███▄ ██▄▄▀█ ▀█▀▄▀█    
    ▄▄█▀▄█▀▀ ▀▄███▄█▀ ██▀█ ▄▀█ ▄▀▄▀▄ ▀ ▀▀▀▀  █ ▀    █    
    ▄  ▄█▀▀▀█▀▀ ▀█  ▄██▄█ █▀▀▀█▀▄▀▄█▀▄█▄▄▀▄▄█▀▀▀██  ▀    
    ▄▄ ██ ▀ █ ▀▀  █▀█ █▄ ▄█ ▀ █▄▀ ▀████ ▀█ ██ ▀ █▀▄ █    
    █▀█ ▀▀▀██▄██▀▀ █▄ █  ███▀▀█▄██ ▀▄▀  █ ▀▀▀▀█▀▀█▀██    
    ▀ ▄█▀▀▀██▀▄▀ ▀▀█▄▀ ▄██ ▄██▀█▄  ▀█▄  ▀██▄▀█▀▄▄▀▀▀█    
    ▀▄████▀█▀▄▄▄▀▀▀▀▀  ▀▀█▀ ▄▀█ ▀█ ▀██▄▀██ ▀▄██   ██▀    
    █▄▄▄ ▄▀██▄▀███ ▄▀ ▄█▀▄█▀ █▄▄█▄▀▀▄▀ █▀ ▀▄▄ ▀█▀▄ ▀█    
    ▄▄▀██ ▀▀█  ▀█▀▄▄█ ▀ █▄▄▀█▀▀▄▄▀ ▀▀▄▀██▀  ▀▀██ █▀▄▀    
    ▄▀▀▀██▀ ▀▄▀▀  █▄▄  ▀ █ █ ▀▀█▀ ▀▄█▀█▄█  ▄  ▀▄ ▀▄▀█    
     █▄▄ ▀▀█▄▄▄▄█ ▀▀▄ ▀▀▀███  ▄▄█▀  ▄▄ ██▀▀ ▄▀█▀ ▀ ▀▀    
    ▀▀▀   ▀ ▄█▄▀ ▀█▄▀  ▄▄▄█▀▀▀██▄█▀█▀▄▀█▀▄█ █▀▀▀█ ▀██    
    █▀▀▀▀▀█ ▄█▄▄ ▀▀▀█▄▄▄ ██ ▀ █ ▀▄▄███▄▄▄▀ ██ ▀ █▄█ ▀    
    █ ███ █ ▄██▀ █▀█▄▄█ ▄ █▀█▀▀▄▀▄▀▄ █▀▄█   ██▀███  ▀    
    █ ▀▀▀ █  ▀▄█▄▄▄▄▀  ▀ ▄▄▄█▄▄▀▄█  ▀▀▀ ▄█▄▄▄▄▀▄▀ ▀      
    ▀▀▀▀▀▀▀ ▀▀▀▀▀ ▀ ▀▀▀▀  ▀ ▀ ▀ ▀▀▀ ▀ ▀▀▀  ▀▀      ▀▀    
                                                         
    egc:election:d9a3ad58f50d2b9bc0ca764e6557eed158d7    
    e9e2f9267e38ebb0f621:117150954:120e7c40b965d13045    
    b92d02d9cb2257057edbb95f9536bd36b3d3ffa1522b17    
```

Now a different node can subscribe using either the QR code or the text.

```
$ egc election subscribe --scan-qrcode # (wave webcam at screen)
```

The text can be nicely formatted, or a messy paste job:

```
$ egc election subscribe --parse-str '''    egc:election:d9a3ad58f50d2b9bc0ca764e6557eed158d7    
    e9e2f9267e38ebb0f621:117150954:120e7c40b965d13045    
    b92d02d9cb2257057edbb95f9536bd36b3d3ffa1522b17    
'''
```

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
