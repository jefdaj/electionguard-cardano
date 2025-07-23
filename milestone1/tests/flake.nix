{
  description = "Multi-container election demo";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
  outputs = { self, nixpkgs, ... }: {
    pkgs = nixpkgs.legacyPackages.x86_64-linux;
    devShells.x86_64-linux.default = self.pkgs.mkShell {
      buildInputs = with self.pkgs; [

        arion
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
