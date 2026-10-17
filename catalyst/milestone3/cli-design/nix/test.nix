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
  cbor2pure = pkgs.python3Packages.callPackage ./cbor2pure.nix {};
  pycardano = pkgs.python3Packages.callPackage ./pycardano.nix {
    inherit cbor2pure;
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
    # cbor2?
    cbor2pure
    pycardano

  ])
