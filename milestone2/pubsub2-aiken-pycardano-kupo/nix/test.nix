# TODO remove once these all work in flake.nix

with import <nixpkgs> {};
let
  kupo = pkgs.callPackage ./kupo.nix {};

in
  kupo
