# This isn't needed in the final code, but I keep it around as a sort of
# documentation for how to incrementally add Python packages to Nix.
# Usage: NIXPKGS_ALLOW_INSECURE=1 nix-shell test.nix

with import <nixpkgs> {};
let
  pytest-runner = pkgs.python3Packages.callPackage ./pytest-runner.nix {};
  py-multiformats-cid = pkgs.python3Packages.callPackage ./py-multiformats-cid.nix {
    inherit pytest-runner;
  };
  aioipfs = pkgs.python3Packages.callPackage ./aioipfs.nix {
    inherit py-multiformats-cid;
  };
  crc8 = pkgs.python3Packages.callPackage ./crc8.nix {};
  pycardano = pkgs.python3Packages.callPackage ./pycardano.nix {
    inherit crc8;
  };

in
  pkgs.python3.withPackages (ps: [

    # from nixpkgs
    ps.py-multiaddr
    ps.py-multihash
    ps.py-multibase

    # packaged here
    pytest-runner # deprecated, but used by py-multiformats-cid
    py-multiformats-cid
    aioipfs
    crc8
    pycardano

  ])
