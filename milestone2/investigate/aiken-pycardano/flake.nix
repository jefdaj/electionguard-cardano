{
  description = "hello world with aiken + pycardano";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
    aiken.url   = "github:aiken-lang/aiken/v1.1.19";
  };

  outputs = { self, nixpkgs, aiken }@inputs:
    let
      pkgs = nixpkgs.legacyPackages.x86_64-linux.extend py312Overlay;

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
