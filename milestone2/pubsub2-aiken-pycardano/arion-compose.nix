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

  networks = import ./networks.nix;

  mkIpfsService = import ./ipfs.nix {
    inherit TMP_DATA;
    inherit (networks) mkStaticIp mkWan;
  };

  mkNodeConfig = import ./node/arion.nix {
    inherit (networks) mkNetworks mkStaticIp mkLan mkWan;
  };

  mkPublisherConfig = import ./publisher/arion.nix {
    inherit TMP_DATA SHARED_CIDS_DIR mkIpfsService;
    inherit (networks) mkNetworks mkStaticIp;
    publisherPkg = flake.packages.x86_64-linux.publisher;
  };

  mkSubscriberConfig = import ./subscriber/arion.nix {
    inherit TMP_DATA SHARED_CIDS_DIR mkIpfsService;
    inherit (networks) mkNetworks mkStaticIp;
    subscriberPkg = flake.packages.x86_64-linux.subscriber;
  };

  mainConfig = {
    project.name = "pubsub";
    enableDefaultNetwork = true; # TODO does this do anything?
    networks = {
      inherit (networks) lan wan;
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
