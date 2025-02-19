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
      # TODO nativeBuildInputs?
      buildInputs = with self.pkgs; [
        arion
        # podman
        docker # TODO remove?
        docker-compose # TODO remove?
        (self.pkgs.python3.withPackages (ps: with ps; [
          dotmap
        ]))
        python3Packages.python
        python3Packages.python-lsp-server
        python3Packages.autopep8
      ];
    };

  };
}
