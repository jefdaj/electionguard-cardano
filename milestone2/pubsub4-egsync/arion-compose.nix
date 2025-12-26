{ pkgs, ... }:

let
  projectConfig = builtins.fromJSON (builtins.readFile (builtins.getEnv "PROJECT_CONFIG"));

  # Shared IPFS mesh network (ipfs <-> ipfs only)
  ipfsMeshNetworkName = "ipfs-mesh-net";

  # Per-triplet egpy net (egpy <-> egsync)
  mkAppNetworkName = mode: n: "${mode}${builtins.toString n}-egpy-net";

  # Per-triplet ipfs net (egsync <-> ipfs)
  mkSyncNetworkName = mode: n: "${mode}${builtins.toString n}-ipfs-net";

  # ---------------------------------------------------------------------------
  # Containers
  # ---------------------------------------------------------------------------

  mkEgpyContainer = mode: scripts_dir: public_dir: private_dir: n: {
    service.image = "ghcr.io/jefdaj/electionguard-python:1.4.0";

    service.volumes = [
      "${scripts_dir}:/scripts/"
      "${public_dir}:/data/public"
      "${private_dir}/${mode}_${builtins.toString n}/egpy:/data/private"
    ];

    service.command = [ "sh" "-c" ''
      while true; do sleep 1000; done
    '' ];

    # Only on its per-triplet app network
    service.networks = [
      (mkAppNetworkName mode n)
    ];
  };

  # Placeholder egsync: isolated between triplets
  mkEgsyncContainer = mode: scripts_dir: public_dir: private_dir: n: {
    service.image = "busybox:latest";

    service.volumes = [
      "${scripts_dir}:/scripts/"
      "${public_dir}:/data/public"
      "${private_dir}/${mode}_${builtins.toString n}/egsync:/data/private"
    ];

    service.command = [ "sh" "-c" ''
      # placeholder for future Flask sync manager
      while true; do sleep 1000; done
    '' ];

    # On two per-triplet nets:
    #   - egpy-net: talk to local egpy
    #   - ipfs-net: talk to local ipfs
    service.networks = [
      (mkAppNetworkName  mode n)
      (mkSyncNetworkName mode n)
    ];
  };

  mkIpfsContainer = mode: private_dir: n: {
    service.image = "ipfs/kubo:latest";

    # one IPFS repo per logical node
    service.volumes = [
      "${private_dir}/${mode}_${builtins.toString n}/ipfs:/data/ipfs"
    ];

    service.command = [ "sh" "-c" ''
      ipfs init --profile server || true
      ipfs daemon --migrate=true --offline=false
    '' ];

    # On:
    #   - its per-triplet ipfs-net (to talk to local egsync)
    #   - global ipfs-mesh-net (to talk to other ipfs nodes)
    service.networks = [
      (mkSyncNetworkName mode n)
      ipfsMeshNetworkName
    ];
  };

  # ---------------------------------------------------------------------------
  # Attr helpers
  # ---------------------------------------------------------------------------

  mkEgpyAttrs = mode: scripts_dir: public_dir: private_dir: n: {
    name = "${mode}${builtins.toString n}-egpy";
    value = mkEgpyContainer mode scripts_dir public_dir private_dir n;
  };

  mkEgsyncAttrs = mode: scripts_dir: public_dir: private_dir: n: {
    name = "${mode}${builtins.toString n}-egsync";
    value = mkEgsyncContainer mode scripts_dir public_dir private_dir n;
  };

  mkIpfsAttrs = mode: private_dir: n: {
    name = "${mode}${builtins.toString n}-ipfs";
    value = mkIpfsContainer mode private_dir n;
  };

  # Produce (egpy, egsync, ipfs) triplets for 1..nVms
  mkTripletAttrsList = dataDir: mode: nVms:
    let
      scripts_dir = "./scripts";
      public_dir  = "${dataDir}/public";
      private_dir = "${dataDir}/private";
      range       = pkgs.lib.range 1 nVms;
    in
    pkgs.lib.concatMap (n: [
      (mkEgpyAttrs   mode scripts_dir public_dir private_dir n)
      (mkEgsyncAttrs mode scripts_dir public_dir private_dir n)
      (mkIpfsAttrs   mode private_dir n)
    ]) range;

  mkServices = cfg:
    builtins.listToAttrs (mkTripletAttrsList cfg.arion.data_dir "admin"     1) //
    builtins.listToAttrs (mkTripletAttrsList cfg.arion.data_dir "device"    cfg.election.devices.count) //
    builtins.listToAttrs (mkTripletAttrsList cfg.arion.data_dir "guardian"  cfg.election.guardians.count) //
    builtins.listToAttrs (mkTripletAttrsList cfg.arion.data_dir "verifier"  cfg.election.verifiers.count);

  # ---------------------------------------------------------------------------
  # Networks
  # ---------------------------------------------------------------------------

  mkNetworks = cfg:
    let
      counts = [
        { mode = "admin";    n = 1; }
        { mode = "device";   n = cfg.election.devices.count; }
        { mode = "guardian"; n = cfg.election.guardians.count; }
        { mode = "verifier"; n = cfg.election.verifiers.count; }
      ];

      # For each triplet: egpy-net and ipfs-net
      perTripletNetworks =
        pkgs.lib.concatMap
          (c: pkgs.lib.concatMap
            (n: [
              {
                name = mkAppNetworkName c.mode n;
                value = { driver = "bridge"; };
              }
              {
                name = mkSyncNetworkName c.mode n;
                value = { driver = "bridge"; };
              }
            ])
            (pkgs.lib.range 1 c.n)
          )
          counts;

    in
    builtins.listToAttrs (
      perTripletNetworks ++ [
        {
          # shared IPFS mesh network (ipfs only)
          name = ipfsMeshNetworkName;
          value = { driver = "bridge"; };
        }
      ]
    );

in {
  config.project.name = projectConfig.arion.project_name;

  config.services = mkServices projectConfig;

  config.networks = mkNetworks projectConfig;
}
