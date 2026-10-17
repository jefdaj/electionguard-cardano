let
  flake = builtins.getFlake (toString ../..);
  inherit (flake) pkgs;

in pkgs // {

  # smuggle in the rest of the flake
  # see https://github.com/hercules-ci/arion/issues/247
  inherit flake;

}
