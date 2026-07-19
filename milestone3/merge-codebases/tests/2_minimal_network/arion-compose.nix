{ pkgs, lib, ... }:
let

  # Shared cardano node data (~15G) for all the dev codebases
  cardanoDir = "../../../../milestone2/cardano-node-ogmios";
  cardanoConfigDir = "${cardanoDir}/config";
  cardanoDataDir   = "${cardanoDir}/data";
  cardanoNetwork   = "preview";

  cardanoService = {
    image = "ghcr.io/intersectmbo/cardano-node:11.0.1";
    command = [
      "run"
      "--config"        "/config/config.json"
      "--database-path" "/data/db"
      "--socket-path"   "/ipc/node.socket"
      "--topology"      "/config/topology.json"
    ];
    volumes = [
      "${cardanoConfigDir}/network/${cardanoNetwork}/cardano-node:/config"
      "${cardanoDataDir}/node-db:/data"
      "${cardanoDataDir}/node-ipc:/ipc"
    ];
    restart = "on-failure";
  };

  ogmiosService = {
    image = "3a21f883f83e"; # TODO upgrade once there's a node 11 compatible pycardano
    restart = "on-failure";
    command = [
      "--host"        "0.0.0.0"
      "--node-socket" "/ipc/node.socket"
      "--node-config" "/config/cardano-node/config.json"
    ];
    volumes = [
      "${cardanoDataDir}/node-ipc:/ipc"
      "${cardanoConfigDir}/network/${cardanoNetwork}:/config"
    ];
    ports = [ "1337:1337" ];
    environment = {
      NETWORK = "preview";
      OGMIOS_PORT = 1337;
    };
  };

  ipfsService = {
    image = "ipfs/kubo:v0.42.0"; 
    restart = "on-failure";
    volumes = [
      { type = "tmpfs"; target = "/data"; }
      "${../../ipfs-init.sh}:/container-init.d/001-config.sh:ro"
      "${../../ipfs-caps.json}:/data/ipfs/libp2p-resource-limit-overrides.json:ro"
    ];
    environment = {
      IPFS_IMPORT_CIDVERSION = "1";
      IPFS_LOGGING           = "error";
      IPFS_TELEMETRY         = "off";
    };
  };

in {
  config.project.name = "egc-minimal";
  config.services = {
    cardano.service = cardanoService;
    ogmios.service  = ogmiosService;
    ipfs.service    = ipfsService;
  };
}
