{ ... }:
let
  parentDir        = "../../milestone2/cardano-node-ogmios";
  cardanoConfigDir = "${parentDir}/config";
  cardanoDataDir   = "${parentDir}/data";
  cardanoNetwork   = "PREVIEW";
  ogmiosPort       = 1337;
in
{
  project.name = "cardano";

  docker-compose.raw = {
    networks.ogmios = {
      internal = true;
      name = "cardano_ogmios";
    };
  };

  services.node.service = {
    image = "ghcr.io/intersectmbo/cardano-node:11.0.1";
    command = [
      "run"
      "--config" "/config/config.json"
      "--database-path" "/data/db"
      "--socket-path" "/ipc/node.socket"
      "--topology" "/config/topology.json"
    ];
    volumes = [
      "${cardanoConfigDir}/network/${cardanoNetwork}/cardano-node:/config"
      "${cardanoDataDir}/node-db:/data"
      "${cardanoDataDir}/node-ipc:/ipc"
    ];
    restart = "on-failure";
    logging = {
      driver = "json-file";
      options = {
        max-size = "400k";
        max-file = "20";
      };
    };
    networks = [ "default" ];
  };

  services.ogmios.service = {
    image = "3a21f883f83e";
    restart = "on-failure";
    command = [
      "--host" "0.0.0.0"
      "--node-socket" "/ipc/node.socket"
      "--node-config" "/config/cardano-node/config.json"
    ];
    volumes = [
      "${cardanoConfigDir}/network/${cardanoNetwork}:/config"
      "${cardanoDataDir}/node-ipc:/ipc"
    ];
    ports = [ "127.0.0.1:${ogmiosPort}:1337" ];
    networks = [ "ogmios" ];
  };
}
