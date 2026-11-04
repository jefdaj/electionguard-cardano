# This spins up a single EGC node with 4 containers:
# - cardano
# - ogmios
# - ipfs
# - egc
#
# It's similar to the tests/env2 environment, except here egc is also packaged
# as a container.

# TODO additional egc service
# TODO ascii art of the container connectivity
# TODO generate docker compose from this

{ pkgs, lib, ... }:
let

  inherit (pkgs) flake; # TODO document
  inherit (pkgs.stdenv.hostPlatform) system;

  # Shared cardano node data (~15G) for all the dev networks
  # Set it manually with `export EGC_CARDANO_DIR=...` before running this
  cardanoDir       = builtins.getEnv "EGC_CARDANO_DIR";
  cardanoConfigDir = "${cardanoDir}/config";
  cardanoDataDir   = "${cardanoDir}/data";
  cardanoNetwork   = "preview";

  # Reference a Docker image based on its pullImage attrs.
  # Note that because Arion is just generating a docker-compose file,
  # this *does not* actually load the image into docker. That needs
  # to be done separately before `arion up`.
  # TODO write that script, and think about the overall ergonomics
  imageName = attrs: "${attrs.finalImageName}:${attrs.finalImageTag}";

  cardanoService = {
    # image = "ghcr.io/intersectmbo/cardano-node:11.0.1";
    image = imageName flake.outputs.packages.${system}.allDockerImages.cardano;
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
    # image = "ghcr.io/intersectmbo/ogmios:v6.14.0.3"; # TODO is this right?
    image = imageName flake.outputs.packages.${system}.allDockerImages.ogmios;
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
    # image = "ipfs/kubo:v0.42.0";
    image = imageName flake.outputs.packages.${system}.allDockerImages.ipfs;
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
  config.project.name = "egc-single-node";
  config.enableDefaultNetwork = true;
  config.services = {
    cardano.service = cardanoService;
    ogmios.service  = ogmiosService;
    ipfs.service    = ipfsService;
  };
}
