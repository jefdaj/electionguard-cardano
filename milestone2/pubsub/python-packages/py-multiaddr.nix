# usage:
# py-multibase = pkgs.python3Packages.callPackage ./py-multibase.nix {
#   inherit pytest-runner;
# };

{ buildPythonPackage
, fetchFromGitHub
, pytest
, pytest-runner
, varint
, base58
, netaddr
, py-cid
, py-multicodec
}:

buildPythonPackage rec {
  name = "py-multiaddr";
  version = "0.0.9";
  src = fetchFromGitHub {
    owner = "multiformats";
    repo = name;
    # last before project was archived
    rev = "e01dbd38f2c0464c0f78b556691d655265018cce";
    sha256 = "WuPAMp6b9XG3xMCANI9sd3M3iZRWwaxoICSV2o4zt9o=";
  };
  nativeBuildInputs = [
    varint
    base58
    netaddr
    py-cid
    py-multicodec
  ];
  nativeCheckInputs = [
    pytest
    pytest-runner
  ];
}
