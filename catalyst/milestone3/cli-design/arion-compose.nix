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
  # TODO put back if it's possible to use egcDocker rather than egc_image name
  # see https://github.com/hercules-ci/arion/issues/247
  # inherit (pkgs) flake;
  # now we can get anything else needed from the flake
  # system = "x86_64-linux";
  # egcApp    = flake.outputs.packages.${system}.default;
  # egcDocker = flake.outputs.packages.${system}.dockerImage;


  ### networks ###

  nodeName = role: index: if builtins.elem role ["funder" "admin"]
                            then role
                            else "${role}${builtins.toString index}";

  ogmiosNetworkName   = role: i: "${nodeName role i}-ogmios-net";
  ipfsNetworkName     = role: i: "${nodeName role i}-ipfs-net";
  ipfsMeshNetworkName = "ipfs-mesh-net";
  cardanoNetworkName  = "cardano-net";

  listOgmiosNetworks = cfg: lib.filter
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
                value = { internal = true; };
              }
              {
                name = ipfsNetworkName c.role n;
                value = { internal = true; };
              }
            ])
            (pkgs.lib.range 1 c.n)
          )
          counts;

    in
    builtins.listToAttrs (
      perPairNetworks ++ [
        {
          # network for Cardano node with bridge to internet
          name = cardanoNetworkName;
          value = { driver = "bridge"; };
        }
        {
          # shared IPFS mesh network with bridge to internet
          name = ipfsMeshNetworkName;

          # Restricting the IPFS net to internal only fixes my internet issues
          # for now, but will prevent testing elections over the internet
          # later...
          value = { driver = "bridge"; };
          # value = { internal = true; };

        }
      ]
    );


  ### services ###

  egcService = egc_image: role: project_name: data_dir: i: {
    service.image = egc_image;
    image.nixBuild = false;
    service.volumes = [
      "${data_dir}/${nodeName role i}/egc:/data/private"
    ];
    service.networks = [
      (ogmiosNetworkName role i)
      (ipfsNetworkName role i)
    ];
    # service.useHostStore = true;
    service.stop_signal = "SIGINT";
    service.environment = 
      let ipfsServiceName = "${project_name}-${nodeName role i}-ipfs-1";
      in {
        IPFS_API_ADDR = "/dns4/${ipfsServiceName}/tcp/5001"; # TODO load properly
      };
  };

  ipfsService = role: data_dir: i: {
    service.image = "ipfs/kubo:v0.42.0"; 
    service.restart = "always"; # TODO does this fix intermittent panics?
    service.volumes = [
      "${data_dir}/${nodeName role i}/ipfs:/data/ipfs"
      "${./ipfs-init.sh}:/container-init.d/001-config.sh:ro"
      "${./ipfs-caps.json}:/data/ipfs/libp2p-resource-limit-overrides.json:ro"
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
      IPFS_LOGGING           = "error";
      IPFS_TELEMETRY         = "off";
      # TODO does this prevent hogging all internet bandwidth?
      # Note that you it takes effect after removing the existing ipfs data.
      # IPFS_PROFILE = "lowpower";
    };
  };

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
    restart = "on-failure"; # TODO remove?
    networks = [ cardanoNetworkName ];
    # TODO how should this look in Arion?
    # logging = {
    #   driver = "json-file";
    #   options = {
    #     max-size = "400k";
    #     max-file = "20";
    #   };
    # };
  };

  ogmiosService = networks: {
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
    inherit networks;
  };

  mkServices = cfg:
    let

      pairEgcAttrs = egc_image: role: project_name: data_dir: i: {
        name = "${nodeName role i}-egc";
        value = egcService egc_image role project_name data_dir i;
      };

      pairIpfsAttrs = role: data_dir: i: {
        name = "${nodeName role i}-ipfs";
        value = ipfsService role data_dir i;
      };

      # Produce (egc, ipfs) pairs for 1..nVms
      pairAttrsList = project_name: egc_image: data_dir: role: nVms:
        let
          range = pkgs.lib.range 1 nVms;
        in
        pkgs.lib.concatMap (i: [
          (pairEgcAttrs egc_image role project_name data_dir i)
          (pairIpfsAttrs role data_dir i)
        ]) range;

      mkServicePairs = pairAttrsList cfg.arion.project_name cfg.arion.egc_image cfg.arion.data_dir;

    in {
      "shared-cardano".service = cardanoService;
      "shared-ogmios".service = ogmiosService (listOgmiosNetworks cfg);
    } //
      builtins.listToAttrs (mkServicePairs "admin"    1) //
      builtins.listToAttrs (mkServicePairs "device"   cfg.election.devices.count) //
      builtins.listToAttrs (mkServicePairs "guardian" cfg.election.guardians.count) //
      builtins.listToAttrs (mkServicePairs "verifier" cfg.election.verifiers.count);


in {
  config.project.name = electionConfig.arion.project_name;
  config.enableDefaultNetwork = false;
  config.networks = mkNetworks electionConfig;
  config.services = mkServices electionConfig;
}
