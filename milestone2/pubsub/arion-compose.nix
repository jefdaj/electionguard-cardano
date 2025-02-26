{ pkgs, ...}:

let
  NODE_CONFIG = "../investigate/cardano-node-ogmios/config";
  NODE_DATA   = "../investigate/cardano-node-ogmios/data";

in {
  config.project.name = "pubsub";
  config.services = {

    cardano-node = {
      service.image = "ghcr.io/intersectmbo/cardano-node:10.1.4";
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
        # # TODO is this needed?
        # # - ./config/network/${NETWORK:-preview}/genesis:/genesis
      ];
      service.restart = "on-failure";

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

    ogmios = {

      # TODO pin to a named version
      # service.image = "cardanosolutions/ogmios:latest";
      service.image = "76902d6a9306";

      service.command = [
        "--host" "0.0.0.0"
        "--node-socket" "/ipc/node.socket"
        "--node-config" "/config/cardano-node/config.json"
      ];
      service.volumes = [
        "${NODE_CONFIG}/network/preview:/config"
        "${NODE_DATA}/node-ipc:/ipc"
      ];
      service.ports = [
        # host:container
        "1337:1337"
      ];
      service.restart = "on-failure";
    };

    # publisher = {
    #   image.contents = [
    #     # TODO nix packages here
    #   ];
    #   service.useHostStore = true;
    #   service.command = [
    #     # TODO args here
    #   ];
    #   service.ports = [
    #     # TODO ipfs port?
    #   ];
    #   service.stop_signal = "SIGINT";
    #   # service.environment.XXX = ...
    # };

    # subscriber = {};

  };
}
