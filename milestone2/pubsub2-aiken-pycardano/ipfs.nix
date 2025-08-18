{ TMP_DATA, mkStaticIp, mkWan }:

let

  # roleName should be like "pub1", "sub1", "pub2", ...
  # ipNumber is the final part of the ip addr like 172.XX.0.{ipNumber}
  mkIpfsService = roleName: subnetNumber:
    let ipAddr = "172.${toString subnetNumber}.0.2";
    in rec {
      # TODO pin named version
      # service.image = "ipfs/kubo:release";
      service.name = roleName + "-ipfs"; # TODO overridden by top attr name?
      # service.image = "e58cd5ca3066";
      service.image = "ipfs/kubo:v0.34.1";
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

in mkIpfsService
