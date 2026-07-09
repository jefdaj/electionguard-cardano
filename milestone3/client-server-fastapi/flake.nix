{
  description = "ElectionGuard+Cardano Client/Server Sketch";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

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

    # TODO electionguard-python input
  };

  outputs = { self, nixpkgs, uv2nix, pyproject-nix, pyproject-build-systems, ... }:
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
        in {
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
              overlay
              pyprojectOverrides
            ]);

        pythonEnv = pythonSet.mkVirtualEnv "egc-client-server-sketch-env" workspace.deps.default;

        kupo = pkgs.callPackage ./nix/kupo.nix {};
        otherDeps = [
          kupo
        ];

    in
    {

      packages.${system} = {

        # This is the Python library code + binaries.
        # TODO also needs cacert?
        default = pythonEnv;

        # TODO also needs cacert?
        dockerImage = pkgs.dockerTools.buildLayeredImage {
          name = "egc-client-server-sketch";
          tag = "0.1.0";
          contents = [
            pythonEnv
            pkgs.coreutils
            pkgs.bashInteractive
          ] ++ otherDeps;
          enableFakechroot = true;
          fakeRootCommands = ''
            mkdir /data; chown 1000:100 /data
            mkdir /tmp ; chmod 1777 /tmp
          '';
          config = {
            # TODO log to stdout? also a logfile under /data?
            Entrypoint = [ "${pythonEnv}/bin/egc" ];
            User = "1000:100"; # TODO named egc user? 1000:1000?
            Env = [
              "PATH=/bin"
            ];
            Labels = {};
            # ExposedPorts = { "8000/tcp" = {}; }; # TODO does this do anything?
          };
        };

      };

      # dev shell with editable install
      devShells.${system}.default =
        let
          editableOverlay = workspace.mkEditablePyprojectOverlay { root = "$PWD"; };
          editablePythonSet = pythonSet.overrideScope editableOverlay;
          venv = editablePythonSet.mkVirtualEnv "egc-client-server-sketch-env" workspace.deps.all;
        in
        pkgs.mkShell {
          packages = with pkgs; [
            jq
            uv
            venv
            cacert # TODO really needed?
            uv
          ] ++ otherDeps;
          env = {
            UV_NO_SYNC = "1";
            UV_PYTHON = "${venv}/bin/python";
            UV_PYTHON_DOWNLOADS = "never";
            PYTHONDONTWRITEBYTECODE = true;

            # TODO are these really needed?
            SSL_CERT_FILE     = "${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt";
            NIX_SSL_CERT_FILE = "${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt";
          };
          shellHook = ''
            unset PYTHONPATH
          '';
        };

    };
}
