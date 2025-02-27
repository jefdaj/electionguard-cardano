# usage:

{ buildPythonPackage
, fetchFromGitHub
, pytest
, pytest-runner
, base58
}:


buildPythonPackage rec {
  name = "py-multiformats-cid";
  version = "0.4.4";
  src = fetchFromGitHub {
    owner = "PancakesArchitect";
    repo = name;
    # master as of 2025-02-27
    rev = "7564c28ef0b2d9bb0b2cba7398e2e4da3cf0084a";
    # comment out and try to build to find proper updated value
    sha256 = "cg/8gYeM+GvQ3oqzSFamx+q6yWTxycmo3gCR3noQrCM=";
  };
  nativeCheckInputs = [
    pytest
    pytest-runner
  ];
  nativeBuildInputs = [
    base58
  ];

  # build-system = [
  #   setuptools
  # ];
  # dependencies = [
  #   # these work
  #   aiohttp
  #   aiofiles
  #   async-timeout
  #   base58
  #   # these would need packaging
  #   gitignore-parser
  #   py-multibase
  #   py-multiaddr
  #   # "py-multiformats-cid"
  # ];
  # pythonRelaxDeps = [
  #   "gitignore-parser"
  # ];
}
