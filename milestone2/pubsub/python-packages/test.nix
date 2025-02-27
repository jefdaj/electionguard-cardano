# TODO remove once these all work in flake.nix

with import <nixpkgs> {};
let
  pytest-runner = pkgs.python3Packages.callPackage ./pytest-runner.nix {};
  py-multiaddr  = pkgs.python3Packages.callPackage ./py-multiaddr.nix {
    inherit pytest-runner;
  };
  py-multibase  = pkgs.python3Packages.callPackage ./py-multibase.nix {
    inherit pytest-runner;
  };
  py-multiformats-cid = pkgs.python3Packages.callPackage ./py-multiformats-cid.nix {
    inherit pytest-runner;
  };
  aioipfs = pkgs.python3Packages.callPackage ./aioipfs.nix {
    inherit py-multibase py-multiaddr py-multiformats-cid;
  };

in
  pkgs.python3.withPackages (ps: with ps; [
    # varint
    pytest-runner
    py-multiaddr
    py-multibase
    py-multiformats-cid
    aioipfs
  ])
