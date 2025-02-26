{ pkgs, ...}:

let

in {
  config.project.name = "pubsub";
  config.services = {

    cardano-node = {
      service.image = "ghcr.io/intersectmbo/cardano-node:10.1.4";
      service.command = [
        "run",
        "--config", "/config/config.json",
        "--database-path", "/data/db",
        "--socket-path", "/ipc/node.socket",
        "--topology", "/config/topology.json"
       ];
      service.volumes = [
        "./node/config/network/preview/cardano-node:/config"
        "./node/data/node-db:/data"
        "./node/data/node-ipc:/ipc"

        # - ./config/network/${NETWORK:-preview}/cardano-node:/config
        # - ./data/node-db:/data
        # - ./data/node-ipc:/ipc
        # # TODO is this needed?
        # # - ./config/network/${NETWORK:-preview}/genesis:/genesis
      ];

      # restart: on-failure
      service.restart = "on-failure";

      # TODO
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
        "--host", "0.0.0.0",
        "--node-socket", "/ipc/node.socket",
        "--node-config", "/config/cardano-node/config.json"
      ];
      service.volumes = [
        "./node/config/network/preview:/config"
        "./node/data/node-ipc:/ipc"
        # - ./config/network/${NETWORK:-preview}:/config
        # - ./data/node-ipc:/ipc
      ];
      service.ports = [
        # host:container
        "1337:1337"
        # - ${OGMIOS_PORT:-1337}:1337
      ];

      # restart: on-failure
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

#   projectConfig = builtins.fromJSON (builtins.readFile ./election.json);
# 
#   mkContainer = mode: scripts_dir: public_dir: private_dir: n:
#   {
# 
#     service.image = "ghcr.io/jefdaj/electionguard-python:1.4.0";
# 
#     service.volumes = [
#       "${scripts_dir}:/scripts/"
#       "${public_dir}:/data/public"
# 
#       # each container only has access to its own private subdir
#       # TODO is it confusing that they're each mounted to the same path?
#       "${private_dir}/${mode}_${builtins.toString n}:/data/private"
#     ];
# 
#     # TODO what's the proper way to keep an arion container running?
#     service.command = [ "sh" "-c" ''
#       while true; do sleep 1000; done
#     '' ];
# 
#   };
# 
#   mkAttrs = mode: scripts_dir: public_dir: private_dir: n: {
#     name = mode + builtins.toString n;
#     value = mkContainer mode scripts_dir public_dir private_dir n;
#   };
# 
#   # TODO pull host bind_mount paths from projectConfig too?
#   mkAttrsList = mode: nVms:
#     map (mkAttrs mode "./scripts" "./data/public" "./data/private") (pkgs.lib.range 1 nVms);
# 
#   mkServices = cfg:
#     builtins.listToAttrs (mkAttrsList "admin" 1) //
#     builtins.listToAttrs (mkAttrsList "device" cfg.election.devices.count) //
#     builtins.listToAttrs (mkAttrsList "guardian" cfg.election.guardians.count);
# 
# in {
#   config.project.name = projectConfig.arion.project_name;
#   config.services = mkServices projectConfig;
# }
