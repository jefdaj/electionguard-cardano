# Nix environment

This is the cleanest, easiest way I can think of for now to make everything Nix-based and reproducible.

It will still depend on having Docker installed system-wide,
but that's pretty standard and I don't think it will be a problem in practice.

1. Overall `flake.nix` (use `nix develop` to get a dev shell)
2. Custom JSON config file with parameters: N guardians, quorum, votes, ...
3. Main Python script runs in dev shell and:

    1. Spins up containers using `arion up -d`, which responds to the config file
    2. Reads the config file itself too
    3. Includes an optional manual mode to step through the election slowly
    4. Runs election commands in the containers
    5. Creates a custom Tmux session to monitor everything?

The [multicontainer demo](./multicontainer_election/) currently does everything except the Tmux session.
