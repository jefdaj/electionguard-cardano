{
  description = "pubsub dApp test";

  inputs = {
    nixpkgs.url     = "github:NixOS/nixpkgs/nixos-24.11";
    aiken.url       = "github:aiken-lang/aiken/v1.1.10";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, aiken, flake-utils }:
    flake-utils.lib.eachDefaultSystem (
      system: let
        pname = "aiken + python dev environment";
        venvDir = ".venv";

        # TODO put this back? it works just as well and overrides system-wide
        # py312Overlay = self: super: {
        #   python312 = super.python312.override {
        #     packageOverrides = pyself: pysuper: {
        #       # TODO it there a way to re-enable the pytest-runner in nixpkgs?
        #       pytest-runner       = pyself.callPackage ./python-packages/pytest-runner.nix       {};
        #       py-multiformats-cid = pyself.callPackage ./python-packages/py-multiformats-cid.nix {};
        #       aioipfs             = pyself.callPackage ./python-packages/aioipfs.nix             {};
        #     };
        #   };
        # };
        # pkgs = nixpkgs.legacyPackages."${system}".extend py312Overlay;

        # TODO remove? the overlay above seems to work the same
        pkgs = nixpkgs.legacyPackages."${system}";
        myPython = pkgs.python312.override {
          # self = python; # TODO what's this?
          packageOverrides = pyself: pysuper: {
            # TODO it there a way to re-enable the pytest-runner in nixpkgs?
            pytest-runner       = pyself.callPackage ./python-packages/pytest-runner.nix       {};
            py-multiformats-cid = pyself.callPackage ./python-packages/py-multiformats-cid.nix {};
            aioipfs             = pyself.callPackage ./python-packages/aioipfs.nix             {};
          };
        };

        myPyPkgList = ps: with ps; [
          aioipfs
          click
          click-default-group
          dotmap
          pygments
        ];

      in
        rec {
          inherit pname;

          # dev shell usage:
          # nix develop
          # cd publisher (or subscriber)
          # python -m venv .venv (first time only)
          # source .venv/bin/activate
          # pip install -r requirements.txt

          devShell = pkgs.mkShell {
            nativeBuildInputs = with pkgs; [

              arion
              file
              jq
              time
              tree

              aiken.packages.x86_64-linux.aiken

              # for publisher and subscriber python scripts
              (myPython.withPackages myPyPkgList)

            ];
        };

        # https://stackoverflow.com/a/78450917
        defaultPackage = myPython.pkgs.buildPythonApplication rec {
          name = "ipfs-download-${version}";
          version = "0.1";
          pyproject = false;
          propagatedBuildInputs = myPyPkgList myPython.pkgs;
          src = ./subscriber/ipfs-download.py;
          dontUnpack = true;
          installPhase = ''
            install -Dm755 "${src}" "$out/bin/ipfs-download"
          '';
        };
      }

    );
}
