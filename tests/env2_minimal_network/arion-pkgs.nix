let
  # The git part prevents .gitignored files being copied to the Nix store.
  flake = builtins.getFlake "git+file://${toString ../..}";
  inherit (flake) pkgs;

in pkgs // {

  # smuggle in the rest of the flake
  # see https://github.com/hercules-ci/arion/issues/247
  inherit flake;

}
