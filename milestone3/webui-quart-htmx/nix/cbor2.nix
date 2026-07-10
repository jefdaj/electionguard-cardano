{
  lib,
  buildPythonPackage,
  fetchPypi,
  pythonOlder,

  # changed by Jeff to fix pycardano v0.14
  # TODO file a nixpkgs issue upstream about defaulting to this?
  withCExtensions ? false,

  # build-system
  setuptools,
  setuptools-scm,

  # tests
  hypothesis,
  pytest-cov-stub,
  pytestCheckHook,
}:

buildPythonPackage rec {
  pname = "cbor2";
  version = "5.8.0";
  pyproject = true;

  disabled = pythonOlder "3.8";

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-sZw1/K6WiKwB73W61dsnMAwlN+tO4A7QfgXYRWoNSTE=";
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

  env = lib.optionalAttrs (!withCExtensions) {
    CBOR2_BUILD_C_EXTENSION = "0";
  };

  passthru = {
    inherit withCExtensions;
  };

  meta = with lib; {
    changelog = "https://github.com/agronholm/cbor2/releases/tag/${version}";
    description = "Python CBOR (de)serializer with extensive tag support";
    mainProgram = "cbor2";
    homepage = "https://github.com/agronholm/cbor2";
    license = licenses.mit;
    maintainers = [ ];
  };
}
