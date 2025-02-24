# Multi-container election demo

Usage:

```bash
nix develop
time ./election.py
```

```bash
# for demos where you want to type on screen
nix develop
./election.py --pause-to-explain
```

```bash
# another way to step through
# good for debugging
nix develop
./election.py --single-step arion_up
./election.py --single-step build_manifest
./election.py --single-step ...
```
