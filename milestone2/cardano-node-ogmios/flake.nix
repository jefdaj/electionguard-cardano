{
  description = "ipfs-cluster test env";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
  outputs = { self, nixpkgs, ... }: {
    pkgs = nixpkgs.legacyPackages.x86_64-linux;
    devShells.x86_64-linux.default = self.pkgs.mkShell {
      buildInputs = with self.pkgs; [
        docker
        docker-compose
      ];
    };
  };
}
