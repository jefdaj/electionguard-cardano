{ pkgs, ...}:

# TODO include code to build electionguard-env from source

let

  multicontainerConfig = builtins.fromJSON (builtins.readFile ./multicontainer.json);

  mkContainer = mode: public_dir: private_dir: n:
  {
    service.image = "electionguard-env"; # TODO hash?
    service.volumes = [
      "./scripts/:/scripts/"
      "${public_dir}:/data/public"
      "${private_dir}/${mode}_${builtins.toString n}:/data/private"
    ];

    # TODO what's the proper way to keep an arion container running?
    service.command = [ "sh" "-c" ''
      while true; do sleep 1000; done
    '' ];

  };

  mkAttrs = mode: public_dir: private_dir: n: {
    name = mode + builtins.toString n;
    value = mkContainer mode public_dir private_dir n;
  };

  mkAttrsList = mode: nVms:
    map (mkAttrs mode "./data/public" "./data/private") (pkgs.lib.range 1 nVms);

  mkServices = cfg:
    builtins.listToAttrs (mkAttrsList "admin" 1) //
    builtins.listToAttrs (mkAttrsList "device" cfg.votingDevices.count) //
    builtins.listToAttrs (mkAttrsList "guardian" cfg.guardians.count);

in {
  config.project.name = multicontainerConfig.project_name;
  config.services = mkServices multicontainerConfig;
}
