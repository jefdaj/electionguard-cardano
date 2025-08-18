{ mkNetworks
, mkStaticIp
, mkLan
, mkWan
}:

let

  # re-use node data
  # this applies starting from the parent dir with arion-compose.nix, which is weird
  NODE_CONFIG = "../investigate/cardano-node-ogmios/config";
  NODE_DATA   = "../investigate/cardano-node-ogmios/data";

  ogmiosPort = 1337; # TODO where should this come from?

  # roleName should be like "node1", "pub1", "sub1", "pub2", ...
  # subnetNumber is the 2nd part of the ip addr like 127.{subnetNumber}.0.N
  mkNodeConfig = roleNumber: subnetNumber:
    let roleName = "node${toString roleNumber}";
    in {
      networks = mkNetworks roleName subnetNumber;
      services = {
        "${roleName}-cardano" = {
          service.image = "ghcr.io/intersectmbo/cardano-node:10.5.1";
          service.command = [
            "run"
            "--config" "/config/config.json"
            "--database-path" "/data/db"
            "--socket-path" "/ipc/node.socket"
            "--topology" "/config/topology.json"
           ];
          service.volumes = [
            "${NODE_CONFIG}/network/preview/cardano-node:/config"
            "${NODE_DATA}/node-db:/data"
            "${NODE_DATA}/node-ipc:/ipc"
            # TODO is this ever needed?
            # - ./config/network/${NETWORK:-preview}/genesis:/genesis
          ];
          service.restart = "on-failure";
          service.networks =
            # Cardano node needs to talk to the internet of course.
            # There should be no need for the other containers to talk to it directly, right?
            # Assuming they're going thru Ogmios.
            (mkStaticIp roleName subnetNumber 2) // mkWan;

          # TODO figure this out
          # service.logging = {
          #   driver = "json-file";
          #   options = {
          #     max-size = "400k";
          #     max-file = "20";
          #   };
          # };
          # logging:
            # driver: "json-file"
            # options:
              # max-size: "400k"
              # max-file: "20"

        };
        "${roleName}-ogmios" = {
          service.image = "cardanosolutions/ogmios:v6.13.0";
          service.command = [
            "--host" "0.0.0.0"
            "--port" "1337"
            "--node-socket" "/ipc/node.socket"
            "--node-config" "/config/cardano-node/config.json"
          ];
          service.volumes = [
            "${NODE_CONFIG}/network/preview:/config"
            "${NODE_DATA}/node-ipc:/ipc"
          ];
          service.ports = [
            # host:container
            "${toString ogmiosPort}:1337"
          ];
          service.restart = "on-failure";
          service.networks =
            # Ogmios should have access to the Cardano node (via its native
            # "node1" network), and other containers should also be able to
            # access it to talk with the Cardano node.
            (mkStaticIp roleName subnetNumber 3) // mkLan;
        };
      };
    };

in mkNodeConfig
