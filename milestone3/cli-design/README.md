CLI Design
==========

The [client/server sketch with Click/FastAPI](../client-server-fastapi) seems good.
Now I'm fleshing out the CLI commands and workflows. Assuming that goes well,
the next step will be to write a version of the election + test scripts that runs
a bash script of `egc` commands per node rather than `docker exec`ing each command
individually.

