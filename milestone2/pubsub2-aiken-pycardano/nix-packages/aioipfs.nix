# usage:

{ buildPythonPackage
, fetchFromGitLab
, setuptools
, distutils
, aiohttp
, aiofiles
, async-timeout
, base58
, gitignore-parser
, py-multibase
, py-multiaddr
, py-multiformats-cid
}:


buildPythonPackage rec {
  name = "aioipfs";
  version = "0.7.1";
  src = fetchFromGitLab {
    owner = "cipres";
    repo = name;

    # latest working commit (april 2024)
    rev = "374cea48a4e1602100dce8a3ed3b2c04dc82c9af";
    sha256 = "iGSiHQOJM8SZXtBlnHPu3lTbt/xXG+9v9q+4D4j15oU=";

    # next commit, does NOT work. has circular import bug
    # also not passing pipeline tests:
    # https://gitlab.com/cipres/aioipfs/-/commits/master?ref_type=HEADS
    # TODO report it to cipres on gitlab
    # rev = "669ba2dddd4196d28e4d2dda07a5471dacdc9c21";
    # sha256 = "uPYBTsGAnOqZ1OJnf954YlcNk8MIH3h1+TRCIA+0vU4=";

  };
  pyproject = true;
  build-system = [
    setuptools
  ];
  dependencies = [
    aiofiles
    aiohttp
    async-timeout
    base58
    distutils
    gitignore-parser
    py-multiaddr
    py-multibase
    py-multiformats-cid
  ];
  pythonRelaxDeps = [
    "gitignore-parser"
  ];
}
