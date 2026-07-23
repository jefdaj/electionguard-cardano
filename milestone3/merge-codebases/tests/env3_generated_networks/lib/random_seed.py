def get_random_seed():
    """Random seed can be set per dev session, which offers a good
    balance between caching and making sure different values work.
    This is the top level main seed. It controls which random configs
    hypothesis generates, and the hashes of the configs control the
    downstream attack random seeds."""
    try:
        seed: int = int(os.environ['EGC_RANDOM_SEED'])
    except KeyError:
        seed = 1234
    return seed
