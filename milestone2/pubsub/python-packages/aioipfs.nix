with import <nixpkgs> {};


pkgs.python3Packages.buildPythonPackage rec {
  name = "aioipfs";
  version = "0.7.1";

  src = fetchFromGitHub {
    owner = "PancakesArchitect";
    repo = name;
    # master as of 2025-02-27
    rev = "5de5c6afa7e0a6f71216af4f42360c460dd289cb";
    # comment out and try to build to find proper updated value
    sha256 = "uPYBTsGAnOqZ1OJnf954YlcNk8MIH3h1+TRCIA+0vU4=";
  };

  pyproject = true;
  build-system = with python3Packages; [
    setuptools
  ];
  dependencies = with python3Packages; [
    # these work
    aiohttp
    aiofiles
    async-timeout
    base58

    # these would need packaging
    gitignore-parser
    # multiaddr
    # "py-multibase"
    # "py-multiformats-cid"
  ];
}
