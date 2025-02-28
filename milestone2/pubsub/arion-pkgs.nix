# based on code in https://github.com/hercules-ci/arion/issues/247

let
  flakeOutputs = builtins.getFlake (toString ./.);
  inherit (flakeOutputs) inputs pkgs packages devShells;

in
  {

    # bits i wanna pass to my containers
    inherit inputs pkgs packages devShells;

    # stuff arion wants to see me return
    inherit (pkgs) lib writeText nix nixos path dockerTools closureInfo runCommand;

  }
