{ pkgs, lib, ... }:
let

  # Shared cardano node data (~15-20G) for all the dev networks
  cardanoDir       = builtins.getEnv "EGC_CARDANO_DIR";
  cardanoConfigDir = "${cardanoDir}/config";
  cardanoDataDir   = "${cardanoDir}/data";
  cardanoNetwork   = "preview";

  cardano = {
    service = {
      image = "ghcr.io/intersectmbo/cardano-node:11.0.1";
      command = [
        "run"
        "--config"        "/config/config.json"
        "--database-path" "/data/db"
        "--socket-path"   "/ipc/node.socket"
        "--topology"      "/config/topology.json"
        "+RTS" "-A16m" "-IO" "-F1.5" "--disable-delayed-os-memory-return" "-RTS"
      ];
      volumes = [
        "${cardanoConfigDir}/network/${cardanoNetwork}/cardano-node:/config"
        "${cardanoDataDir}/node-db:/data"
        "${cardanoDataDir}/node-ipc:/ipc"
        # TODO custom topology? or not needed here?
      ];
      restart = "no"; # TODO "on-failure" for production?
      stop_signal = "SIGINT";
      stop_grace_period = "5m"; # minimize chance of unclean shutdown
    };

    # Arion doesn't have pre-made options for these, but we can still insert
    # them directly in the compose output.
    out.service = {
      oom_score_adj = -500; # kill other processes first
      security_opt = [ "seccomp=${cardanoDir}/seccomp.json" ]; # allow uring calls needed for LSM
    };
  };

  ogmios = {
    service = {
      # image = "jefdaj/ogmios-nix-docker:latest";
      image = "ghcr.io/intersectmbo/ogmios:v6.14.0.3";
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
  };

  ipfs = {
    service = {
      image = "ipfs/kubo:v0.42.0"; 
      restart = "on-failure";
      volumes = [
        { type = "tmpfs"; target = "/data"; }
        "${../../ipfs/ipfs-init.sh}:/container-init.d/001-config.sh:ro"
        "${../../ipfs/ipfs-caps.json}:/data/ipfs/libp2p-resource-limit-overrides.json:ro"
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
  };

in {
  config.project.name = "egc-env2";
  config.enableDefaultNetwork = true;
  config.services = {
    inherit cardano ogmios ipfs;
    # cardano = cardanoService;
    # ogmios  = ogmiosService;
    # ipfs    = ipfsService;
  };
}
