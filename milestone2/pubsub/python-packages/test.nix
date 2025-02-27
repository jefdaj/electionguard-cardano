with import <nixpkgs> {};
let
  pytest-runner = pkgs.python3Packages.callPackage ./pytest-runner.nix {};
  py-multibase  = pkgs.python3Packages.callPackage ./py-multibase.nix {
    inherit pytest-runner;
  };

in
  py-multibase
