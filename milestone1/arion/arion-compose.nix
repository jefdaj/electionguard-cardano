{ pkgs, ...}:

let

  testConfig = builtins.fromJSON (builtins.readFile ./test-config.json);

  mkContainer = mode: port:
  {
    service.image = "electionguard/electionguard-web-api:1.0.4"; # latest
    service.environment.API_MODE = mode;
    service.environment.PORT = port;
    service.ports  = [
      # host:container
      (builtins.toString port + ":" + builtins.toString port)
    ];
    # service.expose = [ ( builtins.toString port) ];
    # service.volumes = [ "${toString ./.}/postgres-data:/var/lib/postgresql/data" ];
  };

  # make a single-vm attrset suitable for merging into the main services attrset
  mkAttrs = mode: startPort: n: {
    name = mode + builtins.toString n;
    value = mkContainer mode (startPort + n);
  };

  # make a list of vm attrsets with the same mode, suitable for merging into the main services attrset
  mkAttrsList = mode: startPort: nVms: map (mkAttrs mode startPort) (pkgs.lib.range 1 nVms);

  # make the entire services attrset
  # the start ports are arbitrary
  mkServices = cfg:
    builtins.listToAttrs (mkAttrsList "guardian" cfg.guardianStartPort cfg.nGuardians) //
    builtins.listToAttrs (mkAttrsList "mediator" cfg.mediatorStartPort cfg.nMediators);

in {
  config.project.name = "electionguard-web-api-test";
  config.services = mkServices testConfig;
}
