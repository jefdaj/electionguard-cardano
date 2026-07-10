{ stdenv, fetchurl, autoPatchelfHook, unzip}:

stdenv.mkDerivation {
  pname = "kupo";
  version = "2.11";
  src = fetchurl {
    url = "https://github.com/CardanoSolutions/kupo/releases/download/v2.11/kupo-v2.11.0-x86_64-linux.zip";
    sha256 = "1xaxnqx0jw0l7krx46bzaabx8klkwv12igcsrg7db855is8zhihn";
  };
  nativeBuildInputs = [ autoPatchelfHook unzip ];
  sourceRoot = ".";
  installPhase = ''
    mkdir -p $out/bin
    cp ./bin/kupo $out/bin/
  '';
}
