{
  description = "Main pubsub flake with Arion";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
  outputs = { self, nixpkgs, ... }: {
    pkgs = nixpkgs.legacyPackages.x86_64-linux;
    devShells.x86_64-linux.default = self.pkgs.mkShell {
      buildInputs = with self.pkgs; [

        arion
        jq
        time
        tree

        ipfs-cluster
        graphviz # for ipfs-cluster-ctl health graph

      ];
    };
  };
}
