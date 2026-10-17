{
  lib,
  buildPythonPackage,
  fetchPypi,
  pythonOlder,
  cbor2,

  # build-system
  setuptools,
  setuptools-scm,

  # tests
  hypothesis,
  pytest-cov-stub,
  pytestCheckHook,
}:

buildPythonPackage rec {
  pname = "cbor2pure";
  version = "5.8.0";
  pyproject = true;

  disabled = pythonOlder "3.8";

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-4D+4fc6zOFGPK05hPzvHEihsRuO1fYPUsLo7YNGnmTI=";
  };

  build-system = [
    setuptools
    setuptools-scm
  ];

  pythonImportsCheck = [ "cbor2" ];

  nativeCheckInputs = [
    hypothesis
    pytest-cov-stub
    pytestCheckHook
  ];

  dependencies = [
    cbor2
  ];

  meta = with lib; {
    description = "A fork of cbor2 without c-extension";
    mainProgram = "cbor2";
    homepage = "https://github.com/cffls/cbor2pure";
    license = licenses.mit;
    maintainers = [ ];
  };
}
