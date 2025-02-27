# based on https://github.com/cpcloud/poetry2nix/commit/eb5b664a84de35b19be7f59a879900c740cbef63

with import <nixpkgs> {};
with pkgs.python3Packages;

buildPythonPackage rec {
  pname = "pytest-runner";
  version = "6.0.1";
  pyproject = true;

  src = pkgs.fetchPypi {
    inherit pname version;
    hash = "sha256-cNRzlYWnAI83v0kzwBP9sye4h4paafy7MxbIiILw9Js=";
  };

  build-system = [
    setuptools
    setuptools-scm
  ];
}
