{ pkgs, lib, ...}:

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

  # roleName is like "node1", "sub1", "sub2", ...
  # subnetNumber is the 2nd part of the ip addr like 127.{subnetNumber}.0.2
  mkNetworks = roleName: subnetNumber: {
    "${roleName}" = {
      name = "${roleName}";
      internal = true; # denies internet access
      ipam = {
        config = [{
          subnet  = "172.${toString subnetNumber}.0.0/16";
          gateway = "172.${toString subnetNumber}.0.1";
        }];
      };
    };
  };

  mkStaticIp = networkName: subnetNumber: ipNumber: {
    "${networkName}" = {
      ipv4_address = "172.${toString subnetNumber}.0.${toString ipNumber}";
    };
  };

  # add to the services.network of a container to give them LAN or WAN access
  # TODO how are you actually supposed to do this?
  mkLan = { lan = {}; };
  mkWan = { wan = {}; };

  # roleName should be like "node1", "pub1", "sub1", "pub2", ...
  # subnetNumber is the 2nd part of the ip addr like 127.{subnetNumber}.0.N
  mkNodeConfig = roleNumber: subnetNumber:
    let roleName = "node${toString roleNumber}";
    in {
      networks = mkNetworks roleName subnetNumber;
      services = {
        "${roleName}-cardano" = {
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
          # service.ports = [
            # host:container
            # TODO remove? forward from network?
            # "1337:1337"
          # ];
          service.restart = "on-failure";
          service.networks =
            # Ogmios should have access to the Cardano node (via its native
            # "node1" network), and other containers should also be able to
            # access it to talk with the Cardano node.
            (mkStaticIp roleName subnetNumber 3) // mkLan;
        };
      };
    };

  # roleName should be like "pub1", "sub1", "pub2", ...
  # ipNumber is the final part of the ip addr like 172.XX.0.{ipNumber}
  mkIpfsService = roleName: subnetNumber:
    let ipAddr = "172.${toString subnetNumber}.0.2";
    in rec {
      # TODO pin named version
      # service.image = "ipfs/kubo:release";
      service.name = roleName + "-ipfs"; # TODO overridden by top attr name?
      service.image = "e58cd5ca3066";
      service.ports = [
        # host:container
        # TODO are these only needed for testing but not production?
        # "${builtins.toString (4000 + portSuffix)}:4001" # ipfs swarm
        # "${builtins.toString (5000 + portSuffix)}:5001" # ipfs api
        # "${builtins.toString (8080 + portSuffix)}:8080" # ipfs gateway
      ];
      service.volumes = [
        "${TMP_DATA}/${service.name}:/data/ipfs"
      ];
      service.environment.IPFS_LOGGING="info";
      service.networks =
        # Ideally we want to simulate IPFS nodes not being on the same
        # computer, so we make them talk over the internet all the time.  But
        # they seem to still be able to talk to each other directly via the
        # pubsub_wan local bridge network. That's not a big deal.
        (mkStaticIp roleName subnetNumber 2) // mkWan;
    };

  # roleNumber is appended to the role name: "sub1", "sub2", ...
  # subnetNumber is the 2nd part of the ip addr like 127.{subnetNumber}.0.3
  mkPublisherConfig = roleNumber: subnetNumber:
    let
      ipfsHost = "172.${toString subnetNumber}.0.2";
      ipfsAddr = "/ip4/${ipfsHost}/tcp/5001";
      pubName  = "pub${toString roleNumber}";
      pubAddr  = "172.${toString subnetNumber}.0.3";
      pubData  = "${TMP_DATA}/${pubName}-publish";
    in {
      networks = mkNetworks pubName subnetNumber;
      services = {
        "${pubName}-ipfs" = mkIpfsService pubName subnetNumber;
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
          service.networks = mkStaticIp pubName subnetNumber 3;
          service.restart = "on-failure";
          # TODO proper syntax for this?
          # service.depends = [
          #   (pubName + "-ipfs")
          # ];
        };
      };
    };

  # roleNumber is appended to the role name: "sub1", "sub2", ...
  # subnetNumber is the 2nd part of the ip addr like 127.{subnetNumber}.0.2
  mkSubscriberConfig = roleNumber: subnetNumber:
    let
      subName  = "sub${toString roleNumber}";
      subData  = "${TMP_DATA}/${subName}-subscribe";
      subAddr  = "172.${toString subnetNumber}.0.3";
      ipfsHost = "172.${toString subnetNumber}.0.2";
      ipfsAddr = "/ip4/${ipfsHost}/tcp/5001";
    in {
      networks = mkNetworks subName subnetNumber;
      services = {
        "${subName}-ipfs" = mkIpfsService subName subnetNumber;
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
          service.networks = mkStaticIp subName subnetNumber 3;
          service.restart = "on-failure";
        };
      };
    };

    mainConfig = {
      project.name = "pubsub";
      enableDefaultNetwork = true; # TODO does this do anything?
      networks = {

        # Add this one to services so they can talk to each other,
        # but not to the wider world.
        lan = {
          internal = true;
          ipam = {
            config = [{
              subnet  = "172.11.0.0/16";
              gateway = "172.11.0.1";
            }];
          };
        };

        # Add this one so they can talk to the wider world.
        # Note they can also talk to each other.
        # TODO is there a way to isolate them so they have to go over the internet?
        wan = {
          ipam = {
            config = [{
              subnet  = "172.12.0.0/16";
              gateway = "172.12.0.1";
            }];
          };
        };

      };
    };

in {
  config = lib.mkMerge [

    mainConfig

    # 1st number is for naming roles: node1, pub1, sub1, sub2, ...
    # 2nd number is for the subnet: 172.{11,12,13,14, ...}.0.0/16
    (mkNodeConfig       1 13)
    (mkPublisherConfig  1 14)
    (mkSubscriberConfig 1 15)
    (mkSubscriberConfig 2 16)

  ];
}
