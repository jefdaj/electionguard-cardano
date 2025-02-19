# Nix environment

This is the cleanest, easiest way I can think of for now to make everything Nix-based and reproducible.

1. Custom JSON config file with parameters: N guardians, quorum, votes, ...
2. Overall `flake.nix` (use `nix develop` to get a dev shell)
3. Main shell script that runs:
3. Main Python script runs in dev shell and:
    a. Spins up containers using `arion up -d`, which responds to the config file
    b. Reads the config file itself too
    c. Includes an optional manual mode to step through the election slowly
    d. Runs election commands in the containers
    e. Creates a custom Tmux session to monitor everything?
