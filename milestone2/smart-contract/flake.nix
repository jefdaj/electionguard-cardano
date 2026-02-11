{
  description = "aiken smart contract";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
    aiken.url   = "github:aiken-lang/aiken/v1.1.21";
  };

  outputs = { self, nixpkgs, aiken }@inputs:
    let
      pkgs = import nixpkgs {
        system = "x86_64-linux";
        config = {};
      };
      devPkgList = ps: with ps; [
        file
        jq
        time
        tree
      ];
      in
        {
          packages.x86_64-linux = rec {
            # TODO any package this time?
          };
          devShells.x86_64-linux = rec {
            default = onchain;
            onchain = pkgs.mkShell {
              nativeBuildInputs = devPkgList pkgs ++ (with pkgs; [
                aiken.packages.x86_64-linux.aiken
              ]);
              shellHook = ''
                echo "running devShells.x86_64-linux.onchain shellHook"
                cd onchain
                echo "aiken version: $(aiken --version)"
              '';
            };
          };
      };
}
