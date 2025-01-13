# electionguard-python dev setup

[Here is my fork](https://github.com/jefdaj/electionguard-python).

## `Makefile` Docker env

The dev instructions assume you're starting from either Mac/Windows or an Ubuntu/Debian Linux distribution. They include a [Makefile](https://github.com/jefdaj/electionguard-python/blob/makefile-docker-env/Makefile) that automates most of the common tasks. It's very nice!

One snag though: I'm weird and on NixOS rather than Debian. That's OK because the Makefile already assumes you'll be using Docker and docker-compose. So I wrote a new top-level [Dockerfile](https://github.com/jefdaj/electionguard-python/blob/makefile-docker-env/Dockerfile). It uses one of the official Python Debian images as a base and installs the system dependencies + Poetry (a Python package manager).

As explained at the top of the [README](https://github.com/jefdaj/electionguard-python/blob/makefile-docker-env/README.md), the only remaining weirdness is that parts of the Makefile should now be run inside the container, and parts on the host system...

```bash
# Run the docker-related make commands in a host nix-shell.
# For example:
nix-shell -p docker-compose gnumake python3
make start-db
```

```bash
# Run the rest in the electionguard-python-makefile-env container.
# For example:
nix-shell -p docker-compose
./makefile-docker-env.sh
make test
make eg-e2e-simple-election
```

[makefile-docker-env.sh](https://github.com/jefdaj/electionguard-python/blob/makefile-docker-env/makefile-docker-env.sh) bind mounts the repo to `/repo`, as well as the data subdirectory to `/data`. I'm not sure whether the data mount is a good idea yet. It's intended to make it easy to retreive generated files after running test elections.

## Fix missing hashes in `poetry.lock`

While setting up the dev environment above, I noticed that all the hashes had disappeared from [poetry.lock](https://github.com/jefdaj/electionguard-python/blob/makefile-docker-env/poetry.lock). This is [a Poetry bug](https://stackoverflow.com/a/73388529) and upgrading 1.1.13 -> 1.1.14 [fixed it](https://github.com/jefdaj/electionguard-python/blob/fix-missing-poetry-lock-hashes/poetry.lock). I also needed to run:

```bash
poetry cache clear pypi --all
poetry lock --no-update
```
