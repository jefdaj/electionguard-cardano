{ pkgs, ... }:

let

  # smuggle flake in via pkgs
  # see https://github.com/hercules-ci/arion/issues/247
  inherit (pkgs) flake;


  ###############
  # json config #
  ###############

  projectConfig = builtins.fromJSON (builtins.readFile (builtins.getEnv "PROJECT_CONFIG"));


  ############
  # networks #
  ############

  # each triplet should be hooked up like:
  # egpy <--1--> egsync <--2--> ipfs <--3--> ipfs mesh

  # 1. per triplet egpy net: egpy <--> egsync
  egpyNetworkName = mode: n: "${mode}${builtins.toString n}-egpy-net";

  # 2. per triplet ipfs net: egsync <--> ipfs
  ipfsNetworkName = mode: n: "${mode}${builtins.toString n}-ipfs-net";

  # 3. shared ipfs net
  ipfsMeshNetworkName = "ipfs-mesh-net";

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
                name = egpyNetworkName c.mode n;
                value = { driver = "bridge"; };
              }
              {
                name = ipfsNetworkName c.mode n;
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


  ##############
  # containers #
  ##############

  egpyContainer = mode: scripts_dir: onchain_dir: private_dir: n: {
    service.image = "ghcr.io/jefdaj/electionguard-python:1.4.0";

    service.volumes = [
      "${scripts_dir}:/scripts/"
      "${onchain_dir}:/data/onchain"
      "${private_dir}/${mode}_${builtins.toString n}/egpy:/data/private"
    ];

    service.command = [ "sh" "-c" ''
      while true; do sleep 1000; done
    '' ];

    # [egpy] <--> egsync
    service.networks = [
      (egpyNetworkName mode n)
    ];
  };

  # TODO write egsync
  # TODO no private_dir needed?
  egsyncContainer = mode: onchain_dir: private_dir: n: {
    # service.image = "busybox:latest";

    service.volumes = [
      "${onchain_dir}:/data/onchain"
      "${private_dir}/${mode}_${builtins.toString n}/egsync:/data/private"
    ];

    # egpy <--> [egsync] <--> ipfs <--> ipfs mesh
    service.networks = [
      (egpyNetworkName mode n)
      (ipfsNetworkName mode n)
    ];

    service.useHostStore = true;
    service.stop_signal = "SIGINT";
    service.command = [
      "egsync.py"
    ];
    service.restart = "on-failure";

    image.enableRecommendedContents = true; # sh, env, misc lightweight files
    image.contents = [
      flake.packages.x86_64-linux.egsync
    ];
 
  };

  ipfsContainer = mode: private_dir: n: {
    service.image = "ipfs/kubo:latest";

    # one IPFS repo per logical node
    service.volumes = [
      "${private_dir}/${mode}_${builtins.toString n}/ipfs:/data/ipfs"
    ];

    # TODO why are the containers shutting down here?
    # TODO go back to how the official docs say to do it?
    service.command = [ "sh" "-c" ''
      ipfs init --profile server || true
      ipfs daemon --migrate=true --offline=false
    '' ];

    # On:
    #   - its per-triplet ipfs-net (to talk to local egsync)
    #   - global ipfs-mesh-net (to talk to other ipfs nodes)
    service.networks = [
      (ipfsNetworkName mode n)
      ipfsMeshNetworkName
    ];
  };


  ############
  # services #
  ############

  egpyAttrs = mode: scripts_dir: onchain_dir: private_dir: n: {
    name = "${mode}${builtins.toString n}-egpy";
    value = egpyContainer mode scripts_dir onchain_dir private_dir n;
  };

  # TODO no private_dir needed?
  egsyncAttrs = mode: onchain_dir: private_dir: n: {
    name = "${mode}${builtins.toString n}-egsync";
    value = egsyncContainer mode onchain_dir private_dir n;
  };

  ipfsAttrs = mode: private_dir: n: {
    name = "${mode}${builtins.toString n}-ipfs";
    value = ipfsContainer mode private_dir n;
  };

  # Produce (egpy, egsync, ipfs) triplets for 1..nVms
  tripletAttrsList = dataDir: mode: nVms:
    let
      scripts_dir = "./egpy_scripts";
      onchain_dir  = "${dataDir}/onchain";
      private_dir = "${dataDir}/private";
      range       = pkgs.lib.range 1 nVms;
    in
    pkgs.lib.concatMap (n: [
      (egpyAttrs   mode scripts_dir onchain_dir private_dir n)
      (egsyncAttrs mode onchain_dir private_dir n)
      (ipfsAttrs   mode private_dir n)
    ]) range;

  mkServices = cfg:
    builtins.listToAttrs (tripletAttrsList cfg.arion.data_dir "admin"    1) //
    builtins.listToAttrs (tripletAttrsList cfg.arion.data_dir "device"   cfg.election.devices.count) //
    builtins.listToAttrs (tripletAttrsList cfg.arion.data_dir "guardian" cfg.election.guardians.count) //
    builtins.listToAttrs (tripletAttrsList cfg.arion.data_dir "verifier" cfg.election.verifiers.count);


in {
  config.project.name = projectConfig.arion.project_name;
  config.services = mkServices projectConfig;
  config.networks = mkNetworks projectConfig;
}
