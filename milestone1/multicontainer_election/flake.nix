{
  description = "Multi-container election demo";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
  outputs = { self, nixpkgs, ... }: {
    pkgs = nixpkgs.legacyPackages.x86_64-linux;
    devShells.x86_64-linux.default = self.pkgs.mkShell {
      buildInputs = with self.pkgs; [

        arion
        jq
        tree

        # python
        # these are only the dependencies for election.py;
        # the other scripts run in the electionguard-python container
        (self.pkgs.python3.withPackages (ps: with ps; [
          click
          click-default-group
          dotmap
          pygments
        ]))

      ];
    };
  };
}
