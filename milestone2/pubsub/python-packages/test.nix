with import <nixpkgs> {};
let
  pytest-runner = pkgs.python3Packages.callPackage ./pytest-runner.nix {};
  py-multiaddr  = pkgs.python3Packages.callPackage ./py-multiaddr.nix {
    inherit pytest-runner;
  };
  py-multibase  = pkgs.python3Packages.callPackage ./py-multibase.nix {
    inherit pytest-runner;
  };
  aioipfs = pkgs.python3Packages.callPackage ./aioipfs.nix {
    inherit py-multibase py-multiaddr;
  };

in
  aioipfs
