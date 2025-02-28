{ pkgs, ...}:

let

  # re-use node data
  NODE_CONFIG = "../investigate/cardano-node-ogmios/config";
  NODE_DATA   = "../investigate/cardano-node-ogmios/data";

  # but the rest be wiped and regenerated whenever
  # data dirs go in here by name: pub1-ipfs, sub1-ipfs, ...
  TMP_DATA = "/tmp/pubsub";

  shared = {
    shared-node = {
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
    shared-ogmios = {
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
  };

  mkIpfsService = namePrefix: portSuffix: rec {
    # TODO pin named version
    # service.image = "ipfs/kubo:release";
    service.name = namePrefix + "-ipfs"; # TODO overridden by top attr name?
    service.image = "e58cd5ca3066";
    service.ports = [
      # host:container
      "${builtins.toString (4000 + portSuffix)}:4001" # ipfs swarm
      "${builtins.toString (5000 + portSuffix)}:5001" # ipfs api
      "${builtins.toString (8080 + portSuffix)}:8080" # ipfs gateway
    ];
    service.volumes = [
      "${TMP_DATA}/${service.name}:/data/ipfs"
    ];
  };

  # mkPublisher = n: portSuffix:
  #   let pubName = "pub" + builtins.toString n;
  #   in {
  #     "${pubName}-ipfs" = mkIpfsService pubName portSuffix;
  #   };

  mkSubscriber = n: portSuffix:
    let subName = "sub" + builtins.toString n;
    in {
      "${subName}-ipfs" = mkIpfsService subName portSuffix;
      "${subName}-download" = {
        image.enableRecommendedContents = true; # TODO what's this again?
        service.useHostStore = true;
        service.stop_signal = "SIGINT";
        service.environment.IPFS_HTTP_PORT = builtins.toString (5000 + portSuffix);
        service.environment.IPFS_DATA_DIR  = "${TMP_DATA}/${subName}-download";
        image.contents = [
          # subscriberDownload
        ];
        # service.command = [
          # "ipfs-download.py"
        # ];
      };
     };

in {
  config.project.name = "pubsub";
  config.services =
    shared; # //
    # mkPublisher  1 1 //
    # mkSubscriber 1 2 //
    # mkSubscriber 2 3;

  # {
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
  # };
}
