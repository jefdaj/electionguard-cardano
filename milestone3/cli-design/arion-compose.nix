{ pkgs, lib, ... }:
let


  ### config ###

  # Main per-election config.
  # Can be written manually or generated via pytest.
  electionConfig = builtins.fromJSON (builtins.readFile (builtins.getEnv "ELECTION_JSON"));

  # Shared cardano node data (~15G) for all the dev codebases
  cardanoDir = "../../milestone2/cardano-node-ogmios";
  cardanoConfigDir = "${cardanoDir}/config";
  cardanoDataDir   = "${cardanoDir}/data";
  cardanoNetwork   = "preview";

  ogmiosPort = 1337;


  ### packages ###

  # smuggle flake in via pkgs
  # see https://github.com/hercules-ci/arion/issues/247
  inherit (pkgs) flake;

  # now we can get anything else needed from the flake
  system = "x86_64-linux";
  egcApp    = flake.outputs.packages.${system}.default;
  egcDocker = flake.outputs.packages.${system}.dockerImage;


  ### networks ###

  nodeName = role: index: if builtins.elem role ["funder" "admin"]
                            then role
                            else "${role}${builtins.toString index}";

  ogmiosNetworkName   = role: i: "${nodeName role i}-ogmios-net";
  ipfsNetworkName     = role: i: "${nodeName role i}-ipfs-net";
  ipfsMeshNetworkName = "ipfs-mesh-net";

  mkOgmiosNetworks = cfg: lib.filter
                            (lib.hasSuffix "-ogmios-net")
                            (builtins.attrNames (mkNetworks cfg));

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


  ### containers ###

  egcContainer = egc_image: role: project_name: records_dir: private_dir: i: {
    service.image = egc_image;
    image.nixBuild = false;
    service.volumes = [
      "${records_dir}:/data/records"
      "${private_dir}/${nodeName role i}/egc:/data/private"
    ];
    service.networks = [
      (ogmiosNetworkName role i)
      (ipfsNetworkName role i)
    ];
    # service.useHostStore = true;
    service.stop_signal = "SIGINT"; # TODO get it to shut down properly
    service.environment = 
      let ipfsContainerName = "${project_name}-${nodeName role i}-ipfs-1";
      in {
        IPFS_API_ADDR = "/dns4/${ipfsContainerName}/tcp/5001";
        PUBLIC_RECORDS_DIR = "/data/records"; # TODO prefix with EGC_ or similar
      };
  };

  ipfsContainer = role: private_dir: i: {
    service.image = "ipfs/kubo:v0.42.0"; 
    service.restart = "always"; # TODO does this fix intermittent panics?
    service.volumes = [
      "${private_dir}/${nodeName role i}/ipfs:/data/ipfs"
    ];
    service.networks = [
      (ipfsNetworkName role i)
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


  ### services ###

  # services.node.service = {
  cardanoService = {
    image = "ghcr.io/intersectmbo/cardano-node:11.0.1";
    command = [
      "run"
      "--config" "/config/config.json"
      "--database-path" "/data/db"
      "--socket-path" "/ipc/node.socket"
      "--topology" "/config/topology.json"
    ];
    volumes = [
      "${cardanoConfigDir}/network/${cardanoNetwork}/cardano-node:/config"
      "${cardanoDataDir}/node-db:/data"
      "${cardanoDataDir}/node-ipc:/ipc"
    ];
    restart = "on-failure";
    # TODO how should this look in Arion?
    # logging = {
    #   driver = "json-file";
    #   options = {
    #     max-size = "400k";
    #     max-file = "20";
    #   };
    # };
    networks = [ "default" ]; # TODO "cardano"?
  };

  # services.ogmios.service = {
  mkOgmiosService = networks: {
    image = "3a21f883f83e";
    restart = "on-failure";
    command = [
      "--host" "0.0.0.0"
      "--node-socket" "/ipc/node.socket"
      "--node-config" "/config/cardano-node/config.json"
    ];
    volumes = [
      "${cardanoConfigDir}/network/${cardanoNetwork}:/config"
      "${cardanoDataDir}/node-ipc:/ipc"
    ];
    ports = [ "127.0.0.1:${toString ogmiosPort}:1337" ];
    # networks = [ "ogmios" ];
    # networks = [ ]; # TODO list of all <pair>-ogmios networks here
    inherit networks;
  };

  egcAttrs = egc_image: role: project_name: records_dir: private_dir: i: {
    name = "${nodeName role i}-egc";
    value = egcContainer egc_image role project_name records_dir private_dir i;
  };

  ipfsAttrs = role: private_dir: i: {
    name = "${nodeName role i}-ipfs";
    value = ipfsContainer role private_dir i;
  };

  # Produce (egc, ipfs) pairs for 1..nVms
  pairAttrsList = project_name: egc_image: dataDir: role: nVms:
    let
      records_dir = "${dataDir}/records";
      private_dir = "${dataDir}/private";
      range       = pkgs.lib.range 1 nVms;
    in
    pkgs.lib.concatMap (i: [
      (egcAttrs egc_image role project_name records_dir private_dir i)
      (ipfsAttrs role private_dir i)
    ]) range;

  # TODO can builtins. be dropped?
  mkServices = cfg:
    {
      cardano.service = cardanoService;
      ogmios.service  = mkOgmiosService (mkOgmiosNetworks cfg);
    } //
    builtins.listToAttrs (pairAttrsList cfg.arion.project_name cfg.arion.egc_image cfg.arion.data_dir "admin"    1) //
    builtins.listToAttrs (pairAttrsList cfg.arion.project_name cfg.arion.egc_image cfg.arion.data_dir "device"   cfg.election.devices.count) //
    builtins.listToAttrs (pairAttrsList cfg.arion.project_name cfg.arion.egc_image cfg.arion.data_dir "guardian" cfg.election.guardians.count) //
    builtins.listToAttrs (pairAttrsList cfg.arion.project_name cfg.arion.egc_image cfg.arion.data_dir "verifier" cfg.election.verifiers.count);


in {
  config.project.name = electionConfig.arion.project_name;
  config.services = mkServices electionConfig;
  config.networks = mkNetworks electionConfig;
}
