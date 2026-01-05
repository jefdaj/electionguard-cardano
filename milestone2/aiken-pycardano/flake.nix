{
  description = "hello world with aiken + pycardano";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
    aiken.url   = "github:aiken-lang/aiken/v1.1.21";
  };

  outputs = { self, nixpkgs, aiken }@inputs:
    let

      basePkgs = import nixpkgs {
        system = "x86_64-linux";
        config = {
          permittedInsecurePackages = [

            # This is a problem for any production use of PyCardano as far as I can tell.
            # TODO either fix it here: github.com/TimothyClaeys/pycose/issues/97
            # TODO or remove cose in favor of something like python-cwt
            # TODO or rewrite TX building in MeshJS rather than PyCardano
            "python3.12-ecdsa-0.19.1"

          ];
        };
      };

      pkgs = basePkgs.extend py312Overlay;

      py312Overlay = self: super: {
        python312 = super.python312.override {
          packageOverrides = pyself: pysuper: {
            cbor2     = pyself.callPackage ./nix-packages/cbor2.nix     {};
            pycardano = pyself.callPackage ./nix-packages/pycardano.nix {};
          };
        };
      };

      devPkgList = ps: with ps; [
        file
        jq
        time
        tree
      ];

      helloPyPkgList = ps: with ps; [
        pycardano
      ];

      in
        {
          # `nix develop`
          devShells.x86_64-linux.default = pkgs.mkShell {
            nativeBuildInputs = devPkgList pkgs ++ (with pkgs; [
              aiken.packages.x86_64-linux.aiken
              (pkgs.python312.withPackages helloPyPkgList)
            ]);
          };
        };
}
