{
  description = "Publisher dev shell with Aiken, PyCardano";

  # based on https://www.zknotes.com/page/python%20development%20flake

  # to activate, type `nix develop` while in the repo dir or a subdir.
  # or use direnv to automatically do so (see .envrc)
  # for best results, don't have a global python installed.  mixing python
  # versions can make for venv problems.

  inputs = {
    nixpkgs.url     = "github:NixOS/nixpkgs/nixos-24.11";
    aiken.url       = "github:aiken-lang/aiken/v1.1.10";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, aiken, flake-utils }:
    flake-utils.lib.eachDefaultSystem (
      system: let
        pname = "aiken + python dev environment";
        pkgs = nixpkgs.legacyPackages."${system}";
        venvDir = ".venv";
      in
        rec {
          inherit pname;

          # `nix develop`
          devShell = pkgs.mkShell {
            nativeBuildInputs = with pkgs; [

              arion
              file
              jq
              time
              tree

              aiken.packages.x86_64-linux.aiken

              python3Packages.python
              python3Packages.distutils # needed for aioipfs
              python3Packages.python-lsp-server
              python3Packages.autopep8

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
        }
    );
}
