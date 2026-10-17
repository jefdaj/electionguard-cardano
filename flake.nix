{
  description = "ElectionGuard+Cardano CLI Design";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    aiken.url   = "github:jefdaj/aiken/nix-flake-update-fix-crate-403";
    arion.url = "github:jefdaj/arion/rm-obsolete-version-attribute";
    electionguard-python = {
      url = "github:jefdaj/electionguard-python";
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

      # These should be changed in sync with:
      # - uv.lock
      # - onchain/aiken.toml
      egcName = "electionguard-cardano";
      egcVersion = "0.6.1";

      inherit (nixpkgs) lib;
      system = "x86_64-linux";

      workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };

      pkgsOverlay = final: prev: {
        python313 = prev.python313.override {
          packageOverrides = pyFinal: pyPrev: {
            # add new packages here:
            # TODO and get some into nixpkgs when you have time
            pytest-runner       = pyFinal.callPackage ./nix/pytest-runner.nix       {};
            py-multiformats-cid = pyFinal.callPackage ./nix/py-multiformats-cid.nix {};
            aioipfs             = pyFinal.callPackage ./nix/aioipfs.nix             {};
            crc8                = pyFinal.callPackage ./nix/crc8.nix                {};
            pycardano           = pyFinal.callPackage ./nix/pycardano.nix           {};
          };
        };
        # keep python313Packages in sync with the overridden interpreter
        python313Packages = final.python313.pkgs;
      };

      # pkgs = nixpkgs.legacyPackages.${system};
      pkgs = import nixpkgs {
        inherit system;
        overlays = [ pkgsOverlay ];
        config.permittedInsecurePackages = [
          "python3.13-ecdsa-0.19.2"
        ];
      };

      python = pkgs.python313;

      pyprojectOverrides = final: prev:
        let
          hacks = pkgs.callPackage pyproject-nix.build.hacks {};

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

          # native zbar dependency for pyzbar
          pyzbar = prev.pyzbar.overrideAttrs (old: {
            postInstall = (old.postInstall or "") + ''
              substituteInPlace $out/${final.python.sitePackages}/pyzbar/zbar_library.py \
                --replace-fail "find_library('zbar')" \
                               '"${pkgs.zbar.lib}/lib/libzbar.so"'
            '';
          });

          # TODO add other custom pkgs here too?
          pycardano = hacks.nixpkgsPrebuilt {
            from = pkgs.python313Packages.pycardano;
            prev = prev.pycardano or {}; # carries name/version/lock metadata
          };

        };

      pythonSet =
        (pkgs.callPackage pyproject-nix.build.packages { inherit python; })
          .overrideScope (lib.composeManyExtensions [
            pyproject-build-systems.overlays.default

            # TODO why doesn't this work?
            # electionguard-python.lib.pyprojectOverrides

            # TODO is this needed?
            electionguard-python.lib.overlay

            (workspace.mkPyprojectOverlay { sourcePreference = "wheel"; })

            pyprojectOverrides
          ]);

      # TODO bundle plutusBlueprints with this too?
      pythonEnv = pythonSet.mkVirtualEnv egcName workspace.deps.default;

      # pkgs = nixpkgs.legacyPackages.${system};
      kupo = pkgs.callPackage ./nix/kupo.nix {};
      runtimeDeps = [
        kupo
        # TODO some of the other pkgs go here instead?
        # pkgs.zbar # TODO is this needed for pyzbar?
      ];

      # This is an actual output; see note below.
      myPkgs = pkgs.extend (final: prev: rec {
        inherit kupo;
        egc       = pythonEnv;
        # TODO put back?
        # python    = python3;
        # python3   = python313;
        # python313 = myPython313;
      });

      devPkgList = ps: with ps; [
        coreutils
        bashInteractive
        arion.packages.x86_64-linux.arion
        file
        jq
        time
        tree
        multitail
      ];

    in
    {

      # This is expected by arion-pkgs.nix
      # See https://github.com/hercules-ci/arion/issues/247
      pkgs = myPkgs;

      packages.${system} = {

        default = pythonEnv;

        # This is the Python library code + binaries.
        # TODO clean up all the misc extra files included here
        inherit pythonEnv;

        # For debugging.
        inherit pythonSet;

        plutusBlueprints = pkgs.stdenv.mkDerivation {
          pname = "egc-plutus-blueprints";
          version = egcVersion;
          src = ./onchain;

          nativeBuildInputs = (devPkgList pkgs) ++ [
            aiken.packages.x86_64-linux.aiken
          ];

          patchPhase = ''
            patchShebangs ./build.sh
          '';

          buildPhase = ''
            export HOME=$TMPDIR
            ./build.sh
          '';

          # TODO the parameterized ones are filtered out of src, right?
          installPhase = ''
            mkdir -p $out
            cp egc-plutus-*.json $out/
          '';
        };

        dockerImage =
          let inherit (self.packages.${system}) plutusBlueprints;
          in
            pkgs.dockerTools.buildLayeredImage {
              name = egcName;
              tag = egcVersion;
              contents = [
                pythonEnv
                pkgs.coreutils
                pkgs.gnugrep
                pkgs.time
                pkgs.findutils
                pkgs.bashInteractive
                pkgs.jq
                plutusBlueprints
                aiken.packages.x86_64-linux.aiken # to apply params
              ] ++ runtimeDeps;
              enableFakechroot = true;
              fakeRootCommands = ''
                mkdir /data; chown 1000:100 /data
                mkdir /data/private; chown 1000:100 /data/private
                mkdir /tmp ; chmod 1777 /tmp
              '';
              config = {
                # TODO log to stdout? also a logfile under /data?
                Entrypoint = [ "${pythonEnv}/bin/egc" ];
                Cmd = [ "node" "run" "--private-dir" "/data/private" ];
                User = "1000:100"; # TODO named egc user? 1000:1000?
                Env = [
                  "PATH=/bin"
                  "EGC_NETWORK_MODE=preview"
                  "EGC_PLUTUS_DIR=${plutusBlueprints}"
                  "EGC_PLUTUS_MODE=burntesttokens-compact"
                  "EGC_WALLET_MODE=scripted"
                  "EGC_WALLET_DIR=/data/private" # TODO /data/private/keys?
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
            venv = editablePythonSet.mkVirtualEnv egcName workspace.deps.all;
            inherit (self.packages.${system}) plutusBlueprints;
          in
          pkgs.mkShell {
            packages = runtimeDeps ++ onchain.nativeBuildInputs ++ (with pkgs; [
              # electionguard-python.packages.${system}.default
              jq
              uv
              venv
              plutusBlueprints
            ]);
            env = {
              UV_NO_SYNC = "1";
              UV_PYTHON = "${venv}/bin/python";
              UV_PYTHON_DOWNLOADS = "never";
              PYTHONDONTWRITEBYTECODE = true;
              EGC_PLUTUS_DIR   = "${plutusBlueprints}";
              EGC_CARDANO_DIR  = "../../milestone2/cardano-node-ogmios"; # TODO point directly to actual path
              EGC_NETWORK_MODE = "preview";
              EGC_PLUTUS_MODE  = "burntesttokens-compact";
              EGC_WALLET_MODE  = "scripted";
              EGC_WALLET_DIR   = "./keys"; # should be in .gitignore
              EGC_DOCKER_IMAGE = "${egcName}:${egcVersion}";

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
               export EGC_CARDANO_DIR="$(realpath "$EGC_CARDANO_DIR")"
               export EGC_WALLET_DIR="$(realpath "./keys")"
               export EGC_HOST_IP=$(curl -s https://api.ipify.org)
               env | grep ^EGC_ | sort
               unset PYTHONPATH
            '';
          };

        };
    };
}
