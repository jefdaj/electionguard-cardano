{ pkgs, ...}:

let

  # smuggle flake in via pkgs
  # see https://github.com/hercules-ci/arion/issues/247
  inherit (pkgs) flake;

  # re-use node data
  NODE_CONFIG = "../investigate/cardano-node-ogmios/config";
  NODE_DATA   = "../investigate/cardano-node-ogmios/data";

  # but the rest be wiped and regenerated whenever
  # data dirs go in here by name: pub1-ipfs, sub1-ipfs, ...
  TMP_DATA = "/tmp/pubsub";

  # temporary workaround to test IPFS sync before smart contracts are written
  SHARED_CIDS_DIR = "${TMP_DATA}/new_cids";

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

  # TODO rename portSuffix now that it also controls ip addr
  mkIpfsService = namePrefix: portSuffix:
    let ipAddr = "172.32.0.${toString (100 + portSuffix)}"; # TODO clean up
    in rec {
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
      service.environment.IPFS_LOGGING="fatal";
      service.networks = { pubsub-custom = { ipv4_address = ipAddr; }; };
    };

  # TODO rename portSuffix now that it also controls ip addr
  mkPublisher = n: portSuffix:
    let
      pubName  = "pub${toString n}";
      pubData  = "${TMP_DATA}/${pubName}-publish";
      pubAddr  = "172.32.0.${toString (100 + portSuffix)}"; # TODO clean up
      ipfsHost = "172.32.0.${toString (150 + portSuffix)}"; # TODO clean up
      ipfsPort = toString 5001;
      ipfsAddr = "/ip4/${ipfsHost}/tcp/${ipfsPort}";
    in {
      "${pubName}-ipfs" = mkIpfsService pubName (portSuffix + 50);
      "${pubName}-publish" = {
        image.enableRecommendedContents = true; # sh, env, misc lightweight files
        service.useHostStore = true;
        service.stop_signal = "SIGINT";
        service.environment.IPFS_API_ADDR = ipfsAddr;
        image.contents = [
          flake.packages.x86_64-linux.publisher
        ];
        service.volumes = [
          "${SHARED_CIDS_DIR}:/new_cids"
          "${pubData}:/upload"
        ];
        service.command = [
          "publish.py"
          "/upload"
          "/new_cids/new_cids.txt"
        ];
        service.networks = { pubsub-custom = { ipv4_address = pubAddr; }; };
        # TODO proper syntax for this?
        # service.depends = [
        #   (pubName + "-ipfs")
        # ];
      };
     };

  # TODO rename portSuffix now that it also controls ip addr
  mkSubscriber = n: portSuffix:
    let
      subName  = "sub" + builtins.toString n;
      subData  = "${TMP_DATA}/${subName}-subscribe";
      subAddr  = "172.32.0.${toString (100 + portSuffix)}"; # TODO clean up
      ipfsHost = "172.32.0.${toString (150 + portSuffix)}"; # TODO clean up
      ipfsPort = toString 5001;
      ipfsAddr = "/ip4/${ipfsHost}/tcp/${ipfsPort}";
    in {
      "${subName}-ipfs" = mkIpfsService subName (portSuffix + 50);
      "${subName}-subscribe" = {
        image.enableRecommendedContents = true; # sh, env, misc lightweight files
        service.useHostStore = true;
        service.stop_signal = "SIGINT";
        service.environment.IPFS_API_ADDR = ipfsAddr;
        service.environment.IPFS_DATA_DIR  = "/data";
        image.contents = [
          flake.packages.x86_64-linux.subscriber
        ];
        service.volumes = [
          "${subData}:/data"
          "${SHARED_CIDS_DIR}:/new_cids"
        ];
        service.command = [
          "subscribe.py"
          "/new_cids/new_cids.txt"
        ];
        service.networks = { pubsub-custom = { ipv4_address = subAddr; }; };
      };
     };

in {
  config.project.name = "pubsub";
  config.services =
    # shared //
    mkPublisher  1 1 //
    mkSubscriber 1 2; # //
    # mkSubscriber 2 3;

    # https://github.com/hercules-ci/arion/blob/main/examples/traefik/arion-compose.nix
    config.networks = {
      # TODO how to get a network per entity (pub1, sub1, sub2, ...)
      pubsub-custom = {
        name = "pubsub-custom";
        ipam = {
          config = [{
            subnet = "172.32.0.0/16";
            gateway = "172.32.0.1";
          }];
        };
      };
    };

}
