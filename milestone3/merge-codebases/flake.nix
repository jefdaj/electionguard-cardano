{
  description = "ElectionGuard+Cardano CLI Design";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    aiken.url   = "github:aiken-lang/aiken/v1.1.21";
    arion.url = "github:jefdaj/arion/rm-obsolete-version-attribute";
    electionguard-python = {
      url = "github:jefdaj/electionguard-python/nix-lib-outputs";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, aiken, arion, electionguard-python,
              uv2nix, pyproject-nix, pyproject-build-systems, ... }:
    let
      inherit (nixpkgs) lib;
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };
      overlay = workspace.mkPyprojectOverlay { sourcePreference = "wheel"; };

      # python = pkgs.python313;
      # python = myPython313;

      myPython313 = pkgs.python313.override {
        packageOverrides = pyself: pysuper: {

          # add new packages here:
          # TODO and get some into nixpkgs when you have time
          pytest-runner       = pyself.callPackage ./nix/pytest-runner.nix       {};
          py-multiformats-cid = pyself.callPackage ./nix/py-multiformats-cid.nix {};
          aioipfs             = pyself.callPackage ./nix/aioipfs.nix             {};
          pycardano           = pyself.callPackage ./nix/pycardano.nix           {};
          cbor2               = pyself.callPackage ./nix/cbor2.nix               {};
          cbor2pure           = pyself.callPackage ./nix/cbor2pure.nix           {};

        };
      };

      pyprojectOverrides = final: prev:
        let
          # lots of the overrides seem to be about adding a build system
          addBuildSystem = names: pkg: pkg.overrideAttrs (old: {
            nativeBuildInputs = (old.nativeBuildInputs or [])
              ++ final.resolveBuildSystem names;
          });
        in
          (electionguard-python.lib.pyprojectOverrides final prev) # TODO is this right?
        // {
          # tweak existing packages here, especially adding build systems:
          # TODO factor out the weird arg format
          gitignore-parser = addBuildSystem {"setuptools" = []; } prev.gitignore-parser;
          varint           = addBuildSystem {"setuptools" = []; } prev.varint;
          python-baseconv  = addBuildSystem {"setuptools" = []; } prev.python-baseconv;
        };

      pythonSet =
        (pkgs.callPackage pyproject-nix.build.packages { python = myPython313; })
          .overrideScope (lib.composeManyExtensions [
            pyproject-build-systems.overlays.default

            # TODO why doesn't this work?
            # electionguard-python.lib.pyprojectOverrides

            # TODO is this needed?
            electionguard-python.lib.overlay

            overlay
            pyprojectOverrides
          ]);

      pythonEnv = pythonSet.mkVirtualEnv "electionguard-cardano" workspace.deps.default;

      kupo = pkgs.callPackage ./nix/kupo.nix {};
      runtimeDeps = [
        kupo
      ];

      # This is an actual output; see note below.
      myPkgs = pkgs.extend (final: prev: rec {
        inherit kupo;
        egc       = pythonEnv;
        python    = python3;
        python3   = python313;
        python313 = myPython313;
      });

      devPkgList = ps: with ps; [
        arion.packages.x86_64-linux.arion
        file
        jq
        time
        tree
      ];

    in
    {

      # temporary for debugging
      inherit workspace;

      # This is expected by arion-pkgs.nix
      # See https://github.com/hercules-ci/arion/issues/247
      pkgs = myPkgs;

      packages.${system} = {

        # This is the Python library code + binaries.
        # TODO also needs cacert?
        default = pythonEnv;

        # TODO also needs cacert?
        dockerImage = pkgs.dockerTools.buildLayeredImage {
          name = "electionguard-cardano";
          tag = "0.2.0";
          contents = [
            pythonEnv
            pkgs.coreutils
            pkgs.bashInteractive
            pkgs.jq
          ] ++ runtimeDeps;
          enableFakechroot = true;
          fakeRootCommands = ''
            mkdir /data; chown 1000:100 /data
            mkdir /tmp ; chmod 1777 /tmp
          '';
          config = {
            # TODO log to stdout? also a logfile under /data?
            Entrypoint = [ "${pythonEnv}/bin/egc" ];
            Cmd = [ "node" "run" ];
            User = "1000:100"; # TODO named egc user? 1000:1000?
            Env = [
              "PATH=/bin"
            ];
            Labels = {};
            # ExposedPorts = { "8000/tcp" = {}; }; # TODO does this do anything?
          };
        };

      };

      devShells.${system} = rec {
        default = offchain;

        # only the aiken-related tools
        onchain = pkgs.mkShell {
          nativeBuildInputs = devPkgList pkgs ++ (with pkgs; [
            aiken.packages.x86_64-linux.aiken
          ]);
          shellHook = ''
            echo "running devShells.x86_64-linux.onchain shellHook"
            cd onchain
            echo "$(aiken --version)"
          '';
        };

        # dev shell with editable install
        offchain =
          let
            editableOverlay = workspace.mkEditablePyprojectOverlay { root = "$PWD"; };
            editablePythonSet = pythonSet.overrideScope editableOverlay;
            venv = editablePythonSet.mkVirtualEnv "electionguard-cardano" workspace.deps.all;
          in
          pkgs.mkShell {
            packages = runtimeDeps ++ onchain.nativeBuildInputs ++ (with pkgs; [
              # electionguard-python.packages.${system}.default
              jq
              uv
              venv
              # cacert # TODO remove?
            ]);
            env = {
              UV_NO_SYNC = "1";
              UV_PYTHON = "${venv}/bin/python";
              UV_PYTHON_DOWNLOADS = "never";
              PYTHONDONTWRITEBYTECODE = true;

              # TODO remove?
              # SSL_CERT_FILE     = "${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt";
              # NIX_SSL_CERT_FILE = "${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt";
            };
            shellHook = ''
               echo "running devShells.x86_64-linux.offchain shellHook"
               echo "$(aiken --version)"
               echo "kupo $(kupo --version)"
               echo "$(python --version)"
               echo "pycardano $(python -c "import importlib.metadata as m; print(m.version('pycardano'))")"
               unset PYTHONPATH
            '';
          };

        };
    };
}
