{
  description = "Election via IPFS + JSON channels";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
  inputs.arion.url = "github:jefdaj/arion/rm-obsolete-version-attribute";
  outputs = { self, nixpkgs, arion, ... }: {
    pkgs = nixpkgs.legacyPackages.x86_64-linux;
    devShells.x86_64-linux.default = self.pkgs.mkShell {
      buildInputs = with self.pkgs; [

        arion.packages.x86_64-linux.arion
        inotify-tools
        jq
        time
        tree

        # python
        # these are only the dependencies for the top-level scripts;
        # scripts/*.py run in the electionguard-python container instead
        (self.pkgs.python3.withPackages (ps: with ps; [
          click
          click-default-group
          dotmap
          hypothesis
          pytest
        ]))

      ];

      PYTHONDONTWRITEBYTECODE = true;

    };
  };
}
