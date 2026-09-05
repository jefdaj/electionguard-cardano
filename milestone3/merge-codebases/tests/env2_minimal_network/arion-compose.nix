{ pkgs, lib, ... }:
let

  # Shared cardano node data (~15G) for all the dev networks
  cardanoDir       = builtins.getEnv "EGC_CARDANO_DIR";
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
    stop_signal = "SIGINT";
    stop_grace_period = "60s"; # default 10s kills it, forcing re-sync on next startup
  };

  ogmiosService = {
    # TODO is this also compatible with pycardano? or do I need to keep the old one?
    # image = "11a9e511ae98"; # TODO upgrade once there's a node 11 compatible pycardano
    image = "cardanosolutions/ogmios:v7.0.0";
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
    ports = [ "1337:1337" ]; # required for host python code to query it?
    environment = {
      NETWORK = cardanoNetwork;
      OGMIOS_PORT = 1337;
    };
    stop_signal = "SIGINT";
    stop_grace_period = "60s";
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
      IPFS_LOGGING           = "info";
      IPFS_TELEMETRY         = "off";
    };
    ports = [
      "4001:4001"           # ipfs swarm
      "127.0.0.1:5001:5001" # api access
    ];
  };

in {
  config.project.name = "egc-env2";
  config.enableDefaultNetwork = true;
  config.services = {
    cardano.service = cardanoService;
    ogmios.service  = ogmiosService;
    ipfs.service    = ipfsService;
  };
}
