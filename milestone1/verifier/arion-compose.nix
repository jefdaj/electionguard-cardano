{ pkgs, ...}:

let

  projectConfig = builtins.fromJSON (builtins.readFile ./verify.json);

  # public outputs of local-election/election.py
  # TODO add verifier output to the public dir too later
  PUBLIC_DIR = toString ../local-election/data/public;

  mkContainer = mode: scripts_dir: public_dir: private_dir: n:
  {

    # service.image = "ghcr.io/jefdaj/electionguard-python:1.4.0";
    service.image = "3517e1782878"; # add-pygraphviz branch (unpublished so far)

    service.volumes = [
      "${scripts_dir}:/scripts/"
      "${public_dir}:/data/public"

      # each container only has access to its own private subdir
      # the verifier shouldn't need it, but just for consistency...
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

  # TODO pull host bind_mount paths from projectConfig too?
  mkAttrsList = mode: nVms:
    map (mkAttrs mode "./scripts" PUBLIC_DIR "./data/private") (pkgs.lib.range 1 nVms);

  mkServices = cfg:
    builtins.listToAttrs (mkAttrsList "verifier" 1);

in {
  config.project.name = projectConfig.arion.project_name;
  config.services = mkServices projectConfig;
}
