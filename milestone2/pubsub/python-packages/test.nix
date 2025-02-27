with import <nixpkgs> {};
let
  # works:
  # pkgs.python3Packages.callPackage pytest-runner {}
  pytest-runner = import ./pytest-runner.nix;

in
  pkgs.python3Packages.callPackage pytest-runner {}
