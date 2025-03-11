{
  description = "Multi-container election demo";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
  outputs = { self, nixpkgs, ... }: {
    pkgs = nixpkgs.legacyPackages.x86_64-linux;
    devShells.x86_64-linux.default = self.pkgs.mkShell {
      buildInputs = with self.pkgs; [

        arion
        inotify-tools
        jq
        time
        tree
        graphviz

        # python
        # these are only the dependencies for the top-level scripts;
        # scripts/*.py run in the electionguard-python container instead
        (self.pkgs.python3.withPackages (ps: with ps; [
          click
          click-default-group
          dotmap
          pygments
          pygraphviz
        ]))

      ];

      shellHook = ''
        scripts_dir=$(realpath scripts)
        echo "scripts_dir: $scripts_dir"
        inotifywait -m "$scripts_dir" -e close_write |
          while read -r directory action file; do
            echo "$file"
            if [[ "$file" =~ verifier.py$ ]]; then
              clear
              ./verify.py
            fi
          done
      '';
    };
  };
}
