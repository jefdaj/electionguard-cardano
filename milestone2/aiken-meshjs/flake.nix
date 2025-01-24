{
  description = "Aiken + MeshJS test env";
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
    aiken.url = "github:aiken-lang/aiken/v1.1.10";
  };
  outputs = { self, nixpkgs, aiken, ... }: {
    pkgs = nixpkgs.legacyPackages.x86_64-linux;
    devShells.x86_64-linux.default = self.pkgs.mkShell {
      buildInputs = [
        aiken.packages.x86_64-linux.aiken
      ];
    };

  };
}
