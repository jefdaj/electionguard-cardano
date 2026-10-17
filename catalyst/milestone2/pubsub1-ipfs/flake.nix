{
  description = "pubsub dApp test #1 ipfs only";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
    arion.url   = "github:jefdaj/arion/rm-obsolete-version-attribute";
  };

  outputs = { self, nixpkgs, arion }:
    let

      # This is an actual output; see note below.
      pkgs = nixpkgs.legacyPackages.x86_64-linux.extend py312Overlay;

      py312Overlay = self: super: {
        python312 = super.python312.override {
          packageOverrides = pyself: pysuper: {
            pytest-runner       = pyself.callPackage ./python-packages/pytest-runner.nix       {};
            py-multiformats-cid = pyself.callPackage ./python-packages/py-multiformats-cid.nix {};
            aioipfs             = pyself.callPackage ./python-packages/aioipfs.nix             {};
          };
        };
      };

      devPkgList = ps: with ps; [
        arion.packages.x86_64-linux.arion
        file
        jq
        time
        tree
      ];

      pubPyPkgList = ps: with ps; [
        aioipfs
        watchdog
      ];

      subPyPkgList = ps: with ps; [
        aioipfs
      ];
      
      # based on https://stackoverflow.com/a/78450917
      singleScriptPyPkg = script: version: pyDeps:
        let scriptName = builtins.baseNameOf script;
        in pkgs.python312.pkgs.buildPythonApplication rec {
          name = "${scriptName}-${version}";
          inherit version;
          pyproject = false;
          propagatedBuildInputs = pyDeps pkgs.python312.pkgs;
          src = script;
          dontUnpack = true;
          installPhase = ''
            install -Dm755 "${src}" "$out/bin/${scriptName}"
          '';
        };

      in
        {

          # This is expected by arion-pkgs.nix
          # See https://github.com/hercules-ci/arion/issues/247
          inherit pkgs;

          # `nix build .#publisher` (or subscriber)
          packages.x86_64-linux = rec {
            publisher  = singleScriptPyPkg ./publisher/publish.py    "0.1" pubPyPkgList;
            subscriber = singleScriptPyPkg ./subscriber/subscribe.py "0.1" subPyPkgList;
          };

          # `nix develop .#publisher` (or subscriber)
          devShells.x86_64-linux = {

            publisher = pkgs.mkShell {
              nativeBuildInputs = (devPkgList pkgs) ++ [
                (pkgs.python312.withPackages pubPyPkgList)
              ];
              shellHook = ''
                echo "running devShells.x86_64-linux.publisher shellHook"
                cd publisher
                # TODO how to mix this with the Nix python pkgs productively?
                # source .venv/bin/activate || python -m venv .venv
                # pip install -r requirements.txt
              '';
            };

            subscriber = pkgs.mkShell {
              nativeBuildInputs = devPkgList pkgs ++ (with pkgs; [
                (pkgs.python312.withPackages subPyPkgList)
              ]);
              shellHook = ''
                echo "running devShells.x86_64-linux.subscriber shellHook"
                cd subscriber
                # TODO how to mix this with the Nix python pkgs productively?
                # source .venv/bin/activate || python -m venv .venv
                # pip install -r requirements.txt
              '';
            };

            # `nix develop`
            # TODO remove? alias to one of the others?
            default = pkgs.mkShell {
              nativeBuildInputs = devPkgList pkgs;
              shellHook = ''
                echo "running devShells.x86_64-linux.default shellHook"
              '';
            };

          };
      };
}
