{
  description = "Mockchain";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";

  outputs = { self, nixpkgs, ... }:
    let

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

      mockchainPyPkgList = ps: with ps; [
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

    in {

      packages.x86_64-linux = rec {
        default = mockchain;
        mockchain = singleScriptPyPkg ./mockchain.py "0.1" mockchainPyPkgList;
      };

      devShells.x86_64-linux = rec {
        default = mockchain;
        mockchain = pkgs.mkShell {
          nativeBuildInputs = devPkgList pkgs ++ [
            (pkgs.python312.withPackages mockchainPyPkgList)
          ];
          PYTHONDONTWRITEBYTECODE = true;
        };
      };

    };
}
