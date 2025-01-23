{
  description = "A very basic flake";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
  inputs.flake-compat.url = "github:edolstra/flake-compat";
  inputs.flake-compat.flake = false;

  outputs = { self, nixpkgs, ... }: {

    pkgs = nixpkgs.legacyPackages.x86_64-linux;

    # packages.x86_64-linux.hello = nixpkgs.legacyPackages.x86_64-linux.hello;
    # defaultPackage.x86_64-linux = self.packages.x86_64-linux.hello;

    devShells.x86_64-linux.default = self.pkgs.mkShell {
      buildInputs = with self.pkgs; [
        arion
        # podman
        docker
        docker-compose
      ];
    };

  };
}
