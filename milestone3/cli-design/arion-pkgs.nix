let
  flake = builtins.getFlake (toString ./.);
  inherit (flake) arionPkgs;

in arionPkgs // {

  # smuggle in the rest of the flake
  # see https://github.com/hercules-ci/arion/issues/247
  # inherit flake;

}
