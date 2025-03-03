# usage:
# pytest-runner = pkgs.python3Packages.callPackage ./pytest-runner.nix {};

{ fetchPypi
, buildPythonPackage
, setuptools
, setuptools-scm
}:

buildPythonPackage rec {
  pname = "pytest-runner";
  version = "6.0.1";
  pyproject = true;
  src = fetchPypi {
    inherit pname version;
    hash = "sha256-cNRzlYWnAI83v0kzwBP9sye4h4paafy7MxbIiILw9Js=";
  };
  build-system = [
    setuptools
    setuptools-scm
  ];
}
