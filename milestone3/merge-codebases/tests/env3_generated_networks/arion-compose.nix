{ pkgs, lib, ... }:
let

  ### config ###

  # Main per-election config.
  # Can be written manually or generated via pytest.
  testConfig = builtins.fromJSON (builtins.readFile (builtins.getEnv "EGC_TEST_JSON"));

  # Shared cardano node data (~15G) for all the dev codebases
  cardanoDir = builtins.getEnv "EGC_CARDANO_DIR";
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

  ogmiosPairNetName   = role: i: "${nodeName role i}-ogmios-net";
  ipfsPairNetName     = role: i: "${nodeName role i}-ipfs-pair-net";
  ipfsSwarmNetName    = role: i: "${nodeName role i}-ipfs-swarm-net";
  # ipfsMeshNetworkName = "ipfs-mesh-net";
  cardanoNetworkName  = "cardano-net";

  listOgmiosNetworks = cfg: lib.filter
                            (lib.hasSuffix "-ogmios-net")
                            (builtins.attrNames (mkNetworks cfg));

  mkNetworks = cfg:
    let
      counts = [
        { role = "admin";    n = 1; }
        { role = "device";   n = cfg.nodes.devices.count; }
        { role = "guardian"; n = cfg.nodes.guardians.number_of_guardians; }
        { role = "verifier"; n = cfg.nodes.verifiers.count; }
      ];

      # For each pair: ogmios-net and ipfs-net
      perPairNetworks =
        pkgs.lib.concatMap
          (c: pkgs.lib.concatMap
            (n: [
              {
                name = ogmiosPairNetName c.role n;
                value = { internal = true; };
              }
              {
                name = ipfsPairNetName c.role n;
                value = { internal = true; };
              }
              {
                name = ipfsSwarmNetName c.role n;
                value = { driver = "bridge"; };
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
        # {
        #   # shared IPFS mesh network with bridge to internet
        #   name = ipfsMeshNetworkName;
        #   # Restricting the IPFS net to internal only fixes my internet issues
        #   # for now, but will prevent testing elections over the internet
        #   # later...
        #   value = {
        #     driver = "bridge";
        #     # TODO does this work to isolate them from each other?
        #     # driver_opts."com.docker.network.bridge.enable_icc" = "false";
        #   };
        # }
      ]
    );


  ### services ###

  egcService = egc_image: role: project_name: data_dir: scripts_dir: i: {
    service.image = egc_image;
    image.nixBuild = false;
    service.command = [
      "node" "run"
      "--private-dir" "/data/private"
    ];
    service.volumes = [
      "${data_dir}/private/${nodeName role i}/egc:/data/private"
      "${data_dir}/qrcodes:/data/qrcodes"
      "${scripts_dir}/${nodeName role i}.sh:/script.sh:ro"
    ];
    service.networks = [
      (ogmiosPairNetName role i)
      (ipfsPairNetName role i)
    ];
    # service.useHostStore = true;
    service.stop_signal = "SIGINT";
    service.environment = 
      let
        ogmiosServiceName = "${project_name}-shared-ogmios-1";
        ipfsServiceName   = "${project_name}-${nodeName role i}-ipfs-1";
      in {
        OGMIOS_HOST = ogmiosServiceName;
        OGMIOS_PORT = toString ogmiosPort;
        IPFS_API_ADDR = "/dns4/${ipfsServiceName}/tcp/5001"; # TODO load properly
      };
  };

  ipfsService = role: data_dir: i: {
    service.image = "ipfs/kubo:v0.42.0"; 
    service.restart = "always"; # TODO does this fix intermittent panics?
    service.volumes = [
      "${data_dir}/private/${nodeName role i}/ipfs:/data/ipfs"
      "${../../ipfs-init.sh}:/container-init.d/001-config.sh:ro"
      # "${../../ipfs-caps.json}:/data/ipfs/libp2p-resource-limit-overrides.json:ro"
    ];
    service.networks = [
      (ipfsPairNetName role i)
      (ipfsSwarmNetName role i)
      # ipfsMeshNetworkName
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
    stop_signal = "SIGINT";
    stop_grace_period = "60s"; # default 10s kills it, forcing re-sync on next startup
    # TODO how should this look in Arion?
    # logging = {
    #   driver = "json-file";
    #   options = {
    #     max-size = "400k";
    #     max-file = "20";
    #   };
    # };
  };

  ogmiosService = perPairNetworks: {
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
    networks = [ cardanoNetworkName ] ++ perPairNetworks;
    stop_signal = "SIGINT";
    stop_grace_period = "60s"; # default 10s kills it, forcing re-sync on next startup
  };

  mkServices = cfg:
    let

      pairEgcAttrs = egc_image: role: project_name: data_dir: scripts_dir: i: {
        name = "${nodeName role i}-egc";
        value = egcService egc_image role project_name data_dir scripts_dir i;
      };

      pairIpfsAttrs = role: data_dir: i: {
        name = "${nodeName role i}-ipfs";
        value = ipfsService role data_dir i;
      };

      # Produce (egc, ipfs) pairs for 1..nVms
      pairAttrsList = project_name: egc_image: data_dir: scripts_dir: role: nVms:
        let
          range = pkgs.lib.range 1 nVms;
        in
        pkgs.lib.concatMap (i: [
          (pairEgcAttrs egc_image role project_name data_dir scripts_dir i)
          (pairIpfsAttrs role data_dir i)
        ]) range;

      mkServicePairs =
        with cfg.arion;
        let
          data_dir = "${cfg.arion.tmpdir}/data";
          scripts_dir = "${cfg.arion.tmpdir}/egc_scripts";
        in
          pairAttrsList project_name egc_image data_dir scripts_dir;

    in {
      "shared-cardano".service = cardanoService;
      "shared-ogmios".service = ogmiosService (listOgmiosNetworks cfg);
    } //
      builtins.listToAttrs (mkServicePairs "admin"    1) //
      builtins.listToAttrs (mkServicePairs "device"   cfg.nodes.devices.count) //
      builtins.listToAttrs (mkServicePairs "guardian" cfg.nodes.guardians.number_of_guardians) //
      builtins.listToAttrs (mkServicePairs "verifier" cfg.nodes.verifiers.count);


in {
  config.project.name = testConfig.arion.project_name;
  config.enableDefaultNetwork = false;
  config.networks = mkNetworks testConfig;
  config.services = mkServices testConfig;
}
