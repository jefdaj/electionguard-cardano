let

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

  # merge into the services.networks of a container to give them LAN or WAN access
  # TODO how are you actually supposed to do this?
  mkLan = { lan = {}; };
  mkWan = { wan = {}; };

in {
  inherit mkNetworks mkStaticIp mkLan mkWan;
}
