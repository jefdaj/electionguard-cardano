{
  description = "pubsub dApp test";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
    aiken.url   = "github:aiken-lang/aiken/v1.1.10";
  };

  outputs = { self, nixpkgs, aiken }:
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
        file
        jq
        time
        tree
      ];

      pubPyPkgList = ps: with ps; [
        aioipfs
        click
        click-default-group
        dotmap
        pygments
        pycardano
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

          # This needs to be one of the outputs. It's expected in arion-pkgs.nix,
          # and I think also by the internal workings of Arion.
          # TODO ask around, read the source code, figure out how this works
          inherit pkgs;

          # `nix build .#publisher` (or subscriber etc)
          packages.x86_64-linux = rec {
            publisher  = singleScriptPyPkg ./publisher/publish.py    "0.1" pubPyPkgList;
            subscriber = singleScriptPyPkg ./subscriber/subscribe.py "0.1" subPyPkgList;
            # default = subscriberDownload;
          };

          devShells.x86_64-linux = {

            # `nix develop .#aiken`
            aiken = pkgs.mkShell {
              nativeBuildInputs = devPkgList pkgs ++ (with pkgs; [
                aiken.packages.x86_64-linux.aiken
              ]);
              shellHook = ''
                echo "running devShells.x86_64-linux.aiken shellHook"
                cd aiken
              '';
            };

            # `nix develop .#publisher`
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

            # `nix develop .#subscriber`
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
