# TODO remove once these all work in flake.nix

with import <nixpkgs> {};
let
  pytest-runner = pkgs.python3Packages.callPackage ./pytest-runner.nix {};
  py-multiformats-cid = pkgs.python3Packages.callPackage ./py-multiformats-cid.nix {
    inherit pytest-runner;
  };
  aioipfs = pkgs.python3Packages.callPackage ./aioipfs.nix {
    inherit py-multiformats-cid;
  };

in
  pkgs.python3.withPackages (ps: with ps; [

    # from nixpkgs
    py-multiaddr
    py-multihash
    py-multibase

    # packaged here
    aioipfs
    py-multiformats-cid
    pytest-runner # TODO is there still a version in nixpkgs somewhere?

  ])
