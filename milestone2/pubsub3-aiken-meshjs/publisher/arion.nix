{ TMP_DATA
, SHARED_CIDS_DIR
, mkNetworks
, mkIpfsService
, mkStaticIp
, publisherPkg
}:

let

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
            publisherPkg
          ];
          service.volumes = [
            "${SHARED_CIDS_DIR}:/new_cids"
            "${pubData}:/upload"
          ];
          # TODO rewrite with meshjs
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

in mkPublisherConfig
