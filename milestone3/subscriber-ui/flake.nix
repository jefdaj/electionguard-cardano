{
  description = "subscriber ui attempt 1";

  inputs = {

    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    aiken.url   = "github:aiken-lang/aiken/v1.1.21";
    arion.url   = "github:jefdaj/arion/rm-obsolete-version-attribute";

  };

  outputs = { self, nixpkgs, aiken, arion }@inputs:
    let

      basePkgs = import nixpkgs {
        system = "x86_64-linux";
        config = {
          permittedInsecurePackages = [

            # This is a problem for any production use of PyCardano as far as I can tell.
            # TODO either fix it here: github.com/TimothyClaeys/pycose/issues/97
            # TODO or remove cose in favor of something like python-cwt
            # TODO or rewrite TX building in MeshJS rather than PyCardano
            # TODO or rely on physical mitigations
            "python3.13-ecdsa-0.19.2"

          ];
        };
      };

      py313Overlay = self: super: {
        python313 = super.python313.override {
          packageOverrides = pyself: pysuper: {
            pytest-runner       = pyself.callPackage ./nix/pytest-runner.nix       {};
            py-multiformats-cid = pyself.callPackage ./nix/py-multiformats-cid.nix {};
            aioipfs             = pyself.callPackage ./nix/aioipfs.nix             {};
            pycardano           = pyself.callPackage ./nix/pycardano.nix           {};
            cbor2               = pyself.callPackage ./nix/cbor2.nix               {};
            cbor2pure           = pyself.callPackage ./nix/cbor2pure.nix           {};
          };
        };
      };

      # This is an actual output; see note below.
      pkgs = basePkgs.extend py313Overlay;

      devPkgList = ps: with ps; [
        arion.packages.x86_64-linux.arion
        file
        jq
        time
        tree
      ];

      offchainPyPkgList = ps: with ps; [
        aioipfs
        click
        click-default-group
        docopt
        dotmap
        pycardano
        pygments
        watchdog
        pytest
        # pytest-instafail
        py-multiformats-cid # exposed on its own to help generate static CID examples
        rich
        deepdiff

        # ui
        flask
        quart
        jinja2
      ];

      kupo = pkgs.callPackage ./nix/kupo.nix {};

      in
        {

          packages.x86_64-linux = rec {
            # TODO package? or just dev shell?
          };

          devShells.x86_64-linux = rec {
            default = pkgs.mkShell {
              nativeBuildInputs = devPkgList pkgs ++ [
                aiken.packages.x86_64-linux.aiken
                (pkgs.python313.withPackages offchainPyPkgList)
                kupo
              ];
              shellHook = ''
                echo "running devShells.x86_64-linux.default shellHook"
                echo "$(aiken --version)"
                echo "kupo $(kupo --version)"
                echo "$(python --version)"
                echo "pycardano $(python -c "import importlib.metadata as m; print(m.version('pycardano'))")"
              '';

              PYTHONDONTWRITEBYTECODE = "1";
            };
          };
      };
}
