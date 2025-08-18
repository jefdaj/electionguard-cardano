{ TMP_DATA
, SHARED_CIDS_DIR
, mkNetworks
, mkIpfsService
, mkStaticIp
, subscriberPkg
}:

let

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
            subscriberPkg
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

in mkSubscriberConfig
