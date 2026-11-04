{
  lib,
  buildPythonPackage,
  fetchPypi,
  setuptools,
}:

buildPythonPackage rec {
  pname = "crc8";
  version = "0.2.1";

  format = "setuptools";

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-LqngoE+7liHa8njafLoMEeX8L3r3TUTTXgiDLTp6TSM=";
  };

  build-system = [
    setuptools
  ];

  # The package has no runtime dependencies.
  # There is no real test suite packaged in the sdist, so imports are the
  # best smoke test we can do.
  pythonImportsCheck = [ "crc8" ];

  meta = with lib; {
    description = "Module that implements the CRC8 hash algorithm for Python 2 and 3";
    homepage = "https://github.com/niccokunzmann/crc8";
    license = licenses.mit;
    maintainers = [ ];
  };
}
