{
  description = "Subscriber dev shell with Python";

  # based on https://www.zknotes.com/page/python%20development%20flake

  # to activate, type `nix develop` while in the repo dir or a subdir.
  # or use direnv to automatically do so (see .envrc)
  # for best results, don't have a global python installed.  mixing python
  # versions can make for venv problems.

  inputs = {
    nixpkgs.url     = "github:NixOS/nixpkgs/nixos-24.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (
      system: let
        pname = "aiken + python dev environment";
        pkgs = nixpkgs.legacyPackages."${system}";
        venvDir = ".venv";

        # TODO clean this up if it works
        pytest-runner = pkgs.python3Packages.callPackage ./pytest-runner.nix {};
        py-multiaddr  = pkgs.python3Packages.callPackage ./py-multiaddr.nix {
          inherit pytest-runner;
        };
        py-multibase  = pkgs.python3Packages.callPackage ./py-multibase.nix {
          inherit pytest-runner;
        };
        py-multiformats-cid = pkgs.python3Packages.callPackage ./py-multiformats-cid.nix {
          inherit pytest-runner;
        };
        aioipfs = pkgs.python3Packages.callPackage ./aioipfs.nix {
          inherit py-multibase py-multiaddr py-multiformats-cid;
        };
	# TODO only use this for build but not dev shell?
	pyPython = python3.withPackages (ps: with ps; [
	  aioipfs
	  click
	  click-default-group
	  dotmap
	  pygments
	]);


      in
        rec {
          inherit pname;

          # `nix develop`
          devShell = pkgs.mkShell {
            nativeBuildInputs = with pkgs; [

              file
              jq
              time
              tree

              python3Packages.python-lsp-server
              python3Packages.autopep8
              python3Packages.python
              python3Packages.distutils # needed for aioipfs

            ];

            shellHook = ''
                # create a virtualenv if there isn't one.

                # DOESN'T install deps for the python app.  Do that once `nix develop` runs with
                # $ cd src
                # $ pip install -r ./requirements.txt

                if [ -d "${venvDir}" ]; then
                  echo "Skipping venv creation, '${venvDir}' already exists"
                else
                  echo "Creating new venv environment in path: '${venvDir}'"
                  # Note that the module venv was only introduced in python 3, so for 2.7
                  # this needs to be replaced with a call to virtualenv
                  python -m venv "${venvDir}"
                  # unescape to attempt use
                  # \$\{pythonPackages.python.interpreter\} -m venv "${venvDir}"
                fi

                # activate our virtual env.
                source "${venvDir}/bin/activate"
              '';
          };

          # `nix build`
          defaultPackage = pkgs.stdenv.mkDerivation rec {
            name = "subscriber-ipfs-download-${version}";
            version = "0.1";
            nativeBuildInputs = with pkgs; [
              myPython
            ];

            src = ./.;
            installPhase = ''
              mkdir -p $out/bin
              # TODO install this in bin properly with wrapper next
              cp ipfs-download.py 
            '';
          };

        }
    );
}
