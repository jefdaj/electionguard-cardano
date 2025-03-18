{ pkgs, ...}:

let

  projectConfig = builtins.fromJSON (builtins.readFile (builtins.getEnv "PROJECT_CONFIG"));

  mkContainer = mode: scripts_dir: public_dir: private_dir: n:
  {

    service.image = "ghcr.io/jefdaj/electionguard-python:1.4.0";

    service.volumes = [
      "${scripts_dir}:/scripts/"
      "${public_dir}:/data/public"

      # each container only has access to its own private subdir
      # TODO is it confusing that they're each mounted to the same path?
      "${private_dir}/${mode}_${builtins.toString n}:/data/private"
    ];

    # TODO what's the proper way to keep an arion container running?
    service.command = [ "sh" "-c" ''
      while true; do sleep 1000; done
    '' ];

  };

  mkAttrs = mode: scripts_dir: public_dir: private_dir: n: {
    name = mode + builtins.toString n;
    value = mkContainer mode scripts_dir public_dir private_dir n;
  };

  mkAttrsList = dataDir: mode: nVms:
    map (mkAttrs mode "./scripts" "${dataDir}/public" "${dataDir}/private") (pkgs.lib.range 1 nVms);

  mkServices = cfg:
    builtins.listToAttrs (mkAttrsList cfg.arion.data_dir "admin" 1) //
    builtins.listToAttrs (mkAttrsList cfg.arion.data_dir "device" cfg.election.devices.count) //
    builtins.listToAttrs (mkAttrsList cfg.arion.data_dir "guardian" cfg.election.guardians.count) //
    builtins.listToAttrs (mkAttrsList cfg.arion.data_dir "verifier" cfg.election.verifiers.count);

in {
  config.project.name = projectConfig.arion.project_name;
  config.services = mkServices projectConfig;
}
