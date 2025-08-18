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

  # merge into the services.networks of a container to give them LAN or WAN access
  # TODO how are you actually supposed to do this?
  mkLan = { lan = {}; };
  mkWan = { wan = {}; };

in {
  inherit mkNetworks mkStaticIp lan wan mkLan mkWan;
}
