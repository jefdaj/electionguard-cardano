# usage:
# py-multibase = pkgs.python3Packages.callPackage ./py-multibase.nix {
#   inherit pytest-runner;
# };

{ buildPythonPackage
, fetchFromGitHub
, pytest
, pytest-runner
}:

buildPythonPackage rec {
  name = "py-multibase";
  version = "1.0.3";
  src = fetchFromGitHub {
    owner = "multiformats";
    repo = name;
    # last before project was archived
    rev = "a49fe7d7651d90f6b572cfa83481e11bef08aa34";
    sha256 = "0+d2+DlDjrGktRV7shfMF3/dCGJsm9RNBDdybvXmLvA=";
  };
  nativeCheckInputs = [
    pytest
    pytest-runner
  ];
}
