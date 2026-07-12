{ pkgs, ... }:

let

  # smuggle flake in via pkgs
  # see https://github.com/hercules-ci/arion/issues/247
  inherit (pkgs) flake;


  ###############
  # json config #
  ###############

  electionConfig = builtins.fromJSON (builtins.readFile (builtins.getEnv "ELECTION_JSON"));


  ############
  # networks #
  ############

  # old for reference:
  # each pair should be hooked up like:
  # egpy <--1--> egsync <--2--> ipfs <--3--> ipfs mesh

  # The idea here is that there should be one persistent Cardano Node + one
  # Ogmios instance, run from a separate Docker compose for now, and then a
  # generated pair of (EGC, IPFS) containers per EGC node. The EGC containers
  # can each talk to Ogmios and to their own IPFS but not to anything else.
  #
  # The IPFS nodes are all networked together, and can also reach the internet.
  # Ogmios only talks to the Cardano node, and the node of course can reach the
  # internet.
  #
  # So each (egc, ipfs) pair should have networks 1, 2, and 3 like this:
  #
  #   egc <--1--> ogmios <--> cardano-node <--> internet
  #   egc <--2--> ipfs <--3--> ipfs mesh + internet
  #
  # 1. <name>-ogmios-net
  # 2. <name>-ipfs-net
  # 3. ipfs-mesh-net
  #
  # Ogmios also has port 1337 open on the host for the webui.

  # per pair ogmios net: egc <--1--> ogmios
  # TODO pass these all to ogmios too
  ogmiosNetworkName = role: n: "${role}${builtins.toString n}-ogmios-net";

  # per pair ipfs net: egpy <--2--> ipfs
  ipfsNetworkName = role: n: "${role}${builtins.toString n}-ipfs-net";

  # shared ipfs net: IPFS <--3--> ipfs mesh
  ipfsMeshNetworkName = "ipfs-mesh-net";

  mkNetworks = cfg:
    let
      counts = [
        { role = "admin";    n = 1; }
        { role = "device";   n = cfg.election.devices.count; }
        { role = "guardian"; n = cfg.election.guardians.count; }
        { role = "verifier"; n = cfg.election.verifiers.count; }
      ];

      # For each pair: ogmios-net and ipfs-net
      perPairNetworks =
        pkgs.lib.concatMap
          (c: pkgs.lib.concatMap
            (n: [
              {
                name = ogmiosNetworkName c.role n;
                value = { driver = "bridge"; }; # TODO not bridge?
              }
              {
                name = ipfsNetworkName c.role n;
                value = { driver = "bridge"; }; # TODO not bridge?
              }
            ])
            (pkgs.lib.range 1 c.n)
          )
          counts;

    in
    builtins.listToAttrs (
      perPairNetworks ++ [
        {
          # shared IPFS mesh network (ipfs only)
          name = ipfsMeshNetworkName;
          value = { driver = "bridge"; }; # TODO does bridge also allow internet?
        }
      ]
    );


  ##############
  # containers #
  ##############

  egcContainer = role: project_name: records_dir: private_dir: n: {
    service.image = egcDocker;

    service.volumes = [
      "${records_dir}:/data/records"
      "${private_dir}/${role}_${builtins.toString n}/egc:/data/private" # TODO no _?
    ];

    service.networks = [
      (ogmiosNetworkName role n)
      (ipfsNetworkName role n)
    ];

    # service.useHostStore = true;
    service.stop_signal = "SIGINT"; # TODO get it to shut down properly

    service.environment = 
      let ipfsContainerName = "${project_name}-${role}${builtins.toString n}-ipfs-1";
      in {
        IPFS_API_ADDR = "/dns4/${ipfsContainerName}/tcp/5001";
        PUBLIC_RECORDS_DIR = "/data/records"; # TODO prefix with EGC_ or similar
      };

  };

  ipfsContainer = role: private_dir: n: {
    service.image = "ipfs/kubo:v0.34.1";

    # TODO does this fix intermittent panics?
    service.restart = "always";

    # one IPFS repo per logical node
    service.volumes = [
      "${private_dir}/${role}_${builtins.toString n}/ipfs:/data/ipfs" # TODO no _?
    ];

    service.networks = [
      (ipfsNetworkName role n)
      ipfsMeshNetworkName
    ];

    service.ports = [
      # host:container
      # TODO are these only needed for testing but not production?
      # TODO add 127.0.0.1?
      # "${builtins.toString (4000 + portSuffix)}:4001" # ipfs swarm
      # "${builtins.toString (5000 + portSuffix)}:5001" # ipfs api
      # "${builtins.toString (8080 + portSuffix)}:8080" # ipfs gateway
    ];
 
    service.environment = {
      IPFS_IMPORT_CIDVERSION = "1";
      IPFS_LOGGING           = "fatal";
      IPFS_TELEMETRY         = "off";
    };
  };


  ############
  # services #
  ############

  egcAttrs = role: project_name: records_dir: private_dir: n: {
    name = "${role}${builtins.toString n}-egc";
    value = egcContainer role project_name records_dir private_dir n;
  };

  ipfsAttrs = role: private_dir: n: {
    name = "${role}${builtins.toString n}-ipfs";
    value = ipfsContainer role private_dir n;
  };

  # Produce (egc, ipfs) pairs for 1..nVms
  pairAttrsList = project_name: dataDir: role: nVms:
    let
      records_dir = "${dataDir}/records";
      private_dir = "${dataDir}/private";
      range       = pkgs.lib.range 1 nVms;
    in
    pkgs.lib.concatMap (n: [
      (egcAttrs  role project_name records_dir private_dir n)
      (ipfsAttrs role private_dir n)
    ]) range;

  # TODO can builtins. be dropped?
  mkServices = cfg:
    builtins.listToAttrs (pairAttrsList cfg.arion.project_name cfg.arion.data_dir "admin"    1) //
    builtins.listToAttrs (pairAttrsList cfg.arion.project_name cfg.arion.data_dir "device"   cfg.election.devices.count) //
    builtins.listToAttrs (pairAttrsList cfg.arion.project_name cfg.arion.data_dir "guardian" cfg.election.guardians.count) //
    builtins.listToAttrs (pairAttrsList cfg.arion.project_name cfg.arion.data_dir "verifier" cfg.election.verifiers.count);


in {
  config.project.name = electionConfig.arion.project_name;
  config.services = mkServices electionConfig;
  config.networks = mkNetworks electionConfig;
}
