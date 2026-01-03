{
  description = "pubsub dApp test #3: ipfs, aiken, meshjs";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
    aiken.url   = "github:aiken-lang/aiken/v1.1.21";
    arion.url   = "github:jefdaj/arion/rm-obsolete-version-attribute";
  };

  outputs = { self, nixpkgs, aiken, arion }@inputs:
    let

      # This is an actual output; see note below.
      # pkgs = nixpkgs.legacyPackages.x86_64-linux.extend py312Overlay;
      pkgs = nixpkgs.legacyPackages.x86_64-linux;

      devPkgList = ps: with ps; [
        arion.packages.x86_64-linux.arion
        file
        jq
        time
        tree
      ];

      in
        {

          # This is expected by arion-pkgs.nix
          # See https://github.com/hercules-ci/arion/issues/247
          inherit pkgs;

          # `nix build .#onchain` etc
          packages.x86_64-linux = rec {
            # publisher  = singleScriptPyPkg ./publisher/publish.py    "0.1" pubPyPkgList;
            # subscriber = singleScriptPyPkg ./subscriber/subscribe.py "0.1" subPyPkgList;
          };

          # `nix develop .#onchain` etc
          devShells.x86_64-linux = {

            # TODO choose one of onchain, pubsub as default shell?

            onchain = pkgs.mkShell {
              nativeBuildInputs = devPkgList pkgs ++ (with pkgs; [
                aiken.packages.x86_64-linux.aiken
                # (pkgs.python312.withPackages onchainPyPkgList)
              ]);
              shellHook = ''
                echo "running devShells.x86_64-linux.onchain shellHook"
                cd onchain
                aiken --version
              '';
            };

            pubsub = pkgs.mkShell {
              nativeBuildInputs = devPkgList pkgs ++ (with pkgs; [
                nodejs
              ]);
              shellHook = ''
                echo "running devShells.x86_64-linux.pubsub shellHook"
                cd pubsub
                echo "npm: $(npm --version)"
              '';
            };

          };
      };
}
