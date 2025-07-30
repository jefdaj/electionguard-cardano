{
  description = "pubsub dApp test #2 ipfs + aiken";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
    aiken.url   = "github:aiken-lang/aiken/v1.1.19";
  };

  outputs = { self, nixpkgs, aiken }@inputs:
    let

      # This is an actual output; see note below.
      pkgs = nixpkgs.legacyPackages.x86_64-linux.extend py312Overlay;

      py312Overlay = self: super: {
        python312 = super.python312.override {
          packageOverrides = pyself: pysuper: {
            pytest-runner       = pyself.callPackage ./nix-packages/pytest-runner.nix       {};
            py-multiformats-cid = pyself.callPackage ./nix-packages/py-multiformats-cid.nix {};
            aioipfs             = pyself.callPackage ./nix-packages/aioipfs.nix             {};
            pycardano           = pyself.callPackage ./nix-packages/pycardano.nix           {};
            cbor2               = pyself.callPackage ./nix-packages/cbor2.nix               {};
          };
        };
      };

      devPkgList = ps: with ps; [
        file
        jq
        time
        tree
      ];

      # TODO remove once debugged and implemented in publisher?
      onchainPyPkgList = ps: with ps; [
        pycardano
      ];

      pubPyPkgList = ps: with ps; [
        aioipfs
        click
        click-default-group
        dotmap
        pygments
        pycardano
        watchdog
      ];

      subPyPkgList = ps: with ps; [
        aioipfs
        click
        click-default-group
        dotmap
        pygments
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

          # `nix build .#publisher` (or subscriber etc)
          packages.x86_64-linux = rec {
            publisher  = singleScriptPyPkg ./publisher/publish.py    "0.1" pubPyPkgList;
            subscriber = singleScriptPyPkg ./subscriber/subscribe.py "0.1" subPyPkgList;
          };

          # `nix develop .#onchain` (or publisher, subscriber, etc)
          devShells.x86_64-linux = {

            onchain = pkgs.mkShell {
              nativeBuildInputs = devPkgList pkgs ++ (with pkgs; [
                aiken.packages.x86_64-linux.aiken
                (pkgs.python312.withPackages onchainPyPkgList)
              ]);
              shellHook = ''
                echo "running devShells.x86_64-linux.onchain shellHook"
                cd onchain
                aiken --version
              '';
            };

            publisher = pkgs.mkShell {
              nativeBuildInputs = (devPkgList pkgs) ++ [
                aiken.packages.x86_64-linux.aiken
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
            default = pkgs.mkShell {
              nativeBuildInputs = devPkgList pkgs;
              shellHook = ''
                echo "running devShells.x86_64-linux.default shellHook"
              '';
            };

          };
      };
}
