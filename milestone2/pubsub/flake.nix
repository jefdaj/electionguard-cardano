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
        pkgs = nixpkgs.legacyPackages."${system}";
        venvDir = ".venv";

        # TODO clean this up if it works
        pytest-runner = pkgs.python3Packages.callPackage
          ./python-packages/pytest-runner.nix {};
        py-multiaddr = pkgs.python3Packages.callPackage
          ./python-packages/py-multiaddr.nix { inherit pytest-runner; };
        py-multibase = pkgs.python3Packages.callPackage
          ./python-packages/py-multibase.nix { inherit pytest-runner; };
        py-multiformats-cid = pkgs.python3Packages.callPackage
          ./python-packages/py-multiformats-cid.nix { inherit pytest-runner; };
        aioipfs = pkgs.python3Packages.callPackage
          ./python-packages/aioipfs.nix {
            inherit py-multibase py-multiaddr py-multiformats-cid;
          };
	# TODO only use this for build but not dev shell?
        # myPython = pkgs.python3.withPackages (ps: with ps; [
        #   aioipfs
        #   click
        #   click-default-group
        #   dotmap
        #   pygments
        # ]);

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
              python3Packages.python
              python3Packages.distutils # needed for aioipfs in dev shell
              python3Packages.python-lsp-server
              python3Packages.autopep8

            ];
        };

        # https://stackoverflow.com/a/78450917
        defaultPackage = pkgs.python3Packages.buildPythonPackage rec {
          name = "subscriber-main";
          version = "0.1";
          pyproject = false;
          # TODO pass these the python used here
          propogatedBuildInputs = with pkgs.python3Packages; [
	    aioipfs
	    click
	    click-default-group
	    dotmap
	    pygments
          ];
          script = ./subscriber/ipfs-download.py;
          dontUnpack = true;
          installPhase = ''
            install -Dm755 "${script}" $out/bin/subscriber-main.py
          '';
        };
      }

    );
}
