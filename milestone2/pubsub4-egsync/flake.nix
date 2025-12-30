{
  description = "Election via IPFS + JSON channels";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
  inputs.arion.url = "github:jefdaj/arion/rm-obsolete-version-attribute";

  outputs = { self, nixpkgs, arion, ... }:
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

      toplevelPyPkgList = ps: with ps; [
        click
        click-default-group
        dotmap
        hypothesis
        pytest
      ];

      egsyncPyPkgList = ps: with ps; [
        # ipfshttpclient
        aioipfs
        pydantic
        requests
        watchdog
        quart
        hypercorn
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

      # This is expected by arion-pkgs.nix
      # See https://github.com/hercules-ci/arion/issues/247
      inherit pkgs;

      # `nix build .#egsync`
      packages.x86_64-linux = {
        egsync = singleScriptPyPkg ./egsync.py "0.1" egsyncPyPkgList;
      };

      devShells.x86_64-linux = rec {

        default = toplevel;

        # TODO better name for this one?
        toplevel = pkgs.mkShell {
          nativeBuildInputs = devPkgList pkgs ++ [
            (pkgs.python312.withPackages toplevelPyPkgList)
          ];
          PYTHONDONTWRITEBYTECODE = true;
        };

        egsync = pkgs.mkShell {
          nativeBuildInputs = devPkgList pkgs ++ [
            (pkgs.python312.withPackages egsyncPyPkgList)
          ];
          PYTHONDONTWRITEBYTECODE = true;
        };

      };
    };
}
