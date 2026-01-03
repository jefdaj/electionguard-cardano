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
          packages.x86_64-linux = {
            # TODO pick a default build?
            pubsub = pkgs.buildNpmPackage {
              pname = "pubsub";
              version = "0.0.1";
              src = ./pubsub;

              # use to update hash:
              # npmDepsHash = pkgs.lib.fakeHash;
              npmDepsHash = "sha256-rqKjXApp9XCRVyNBB3xGwjpkd5mgeRr1ktSi2JiWsq4=";

              buildInputs = with pkgs; [
                nodejs
                nodePackages.npm
              ];

              # prevent packages (node-datachannel) from attempting network access during build
              npmFlags = [ "--ignore-scripts" ];

              # TODO remove? seems to work with or without equally well
              buildPhase = ''
                npm run build
              '';

              # TODO clean up or replace with something more idiomatic
              installPhase = ''
                mkdir -p $out/bin
                # copy sources or build artifacts
                mkdir -p $out/app
                cp -r dist node_modules $out/app/
                # create an executable wrapper
                cat > $out/bin/pubsub <<EOF
                #!${pkgs.bash}/bin/bash
                # run via node from Nix store
                exec ${pkgs.nodejs}/bin/node $out/app/dist/index.js "\$@"
                EOF
                chmod +x $out/bin/pubsub
              '';
            };
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
              packages = devPkgList pkgs ++ (with pkgs; [
                # TODO? nodePackages.typescript-language-server
                nodejs_24 # lts as of spring 2026
                nodePackages.typescript
              ]);
              shellHook = ''
                echo "running devShells.x86_64-linux.pubsub shellHook"
                cd pubsub
                echo "Node version: $(node --version)"
                echo "TypeScript version: $(tsc --version)"
              '';
            };

          };
      };
}
