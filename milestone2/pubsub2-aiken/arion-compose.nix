{ pkgs, lib, ...}:

let

  # smuggle flake in via pkgs
  # see https://github.com/hercules-ci/arion/issues/247
  inherit (pkgs) flake;

  # but the rest be wiped and regenerated whenever
  # data dirs go in here by name: pub1-ipfs, sub1-ipfs, ...
  TMP_DATA = "/tmp/pubsub";

  # temporary workaround to test IPFS sync before smart contracts are written
  SHARED_CIDS_DIR = "${TMP_DATA}/new_cids";

  utils = import ./utils.nix;
  inherit (utils) mkNetworks mkStaticIp mkLan mkWan;

  mkIpfsService = import ./ipfs.nix { inherit TMP_DATA mkStaticIp mkWan; };

  mkNodeConfig = import ./node/arion.nix;

  mkPublisherConfig = import ./publisher/arion.nix {
    inherit TMP_DATA SHARED_CIDS_DIR mkNetworks mkIpfsService mkStaticIp;
    publisherPkg = flake.packages.x86_64-linux.publisher;
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
