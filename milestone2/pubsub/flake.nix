{
  description = "pubsub dApp test";

  inputs = {
    nixpkgs.url     = "github:NixOS/nixpkgs/nixos-24.11";
    aiken.url       = "github:aiken-lang/aiken/v1.1.10";
    # flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, aiken, flake-utils }:
    let
    # flake-utils.lib.eachDefaultSystem (
      # system: let
        # pname = "aiken + python dev environment"; # TODO what's this for?
        # venvDir = ".venv";

        pkgs = nixpkgs.legacyPackages.x86_64-linux.extend py312Overlay;

        py312Overlay = self: super: {
          python312 = super.python312.override {
            packageOverrides = pyself: pysuper: {
              # TODO it there a way to re-enable the pytest-runner in nixpkgs?
              pytest-runner       = pyself.callPackage ./python-packages/pytest-runner.nix       {};
              py-multiformats-cid = pyself.callPackage ./python-packages/py-multiformats-cid.nix {};
              aioipfs             = pyself.callPackage ./python-packages/aioipfs.nix             {};
            };
          };
        };

        myPyPkgList = ps: with ps; [
          aioipfs
          click
          click-default-group
          dotmap
          pygments
        ];
        
        # based on https://stackoverflow.com/a/78450917
        singleScriptPyPkg = script: pyDeps:
          pkgs.python312.pkgs.buildPythonApplication rec {
            name = "ipfs-download-${version}";
            version = "0.1";
            pyproject = false;
            propagatedBuildInputs = pyDeps pkgs.python312.pkgs;
            src = script;
            dontUnpack = true;
            installPhase = ''
              install -Dm755 "${src}" "$out/bin/${builtins.baseNameOf script}"
            '';
          };

      in
        {
          # inherit pname;

          # dev shell usage:
          # nix develop
          # cd publisher (or subscriber)
          # python -m venv .venv (first time only)
          # source .venv/bin/activate
          # pip install -r requirements.txt

          # This needs to be one of the outputs. It's expected in arion-pkgs.nix,
          # and I think also by the internal workings of Arion.
          inherit pkgs;

          # TODO split into separate devShells for publisher, subscriber, aiken?
          devShells.default = pkgs.mkShell {
            nativeBuildInputs = with pkgs; [

              arion
              file
              jq
              time
              tree

              aiken.packages.x86_64-linux.aiken

              # for publisher and subscriber python scripts
              (pkgs.python312.withPackages myPyPkgList)

            ];
          };

          # TODO rename publish.py and subscribe.py for simplicity
          packages = rec {
            publisherUpload    = singleScriptPyPkg ./publisher/ipfs-upload.py    myPyPkgList;
            subscriberDownload = singleScriptPyPkg ./subscriber/ipfs-download.py myPyPkgList;
            # default = subscriberDownload;
          };

      };
}
