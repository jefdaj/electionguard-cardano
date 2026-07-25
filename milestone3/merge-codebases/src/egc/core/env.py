import os
from pathlib import Path

# Currently this doesn't hold all the settings. It just holds the ones that are
# set manually; anything auto-derived from them can go in other modules as
# needed.
# TODO any other settings that would warrent a config module here?

# Which plutus variant to use. Current options:
# burntesttokens
# burntesttokens-traced
# TODO production
# TODO production-traced
EGC_PLUTUS_MODE = os.environ.get('EGC_PLUTUS_MODE', 'burntesttokens-traced').lower()

# Which network to deploy to. This is separate from the plutus mode because we
# might want to deploy the production contract to a test network.
# Only 'preview' is supported so far.
# TODO preprod?
# TODO mainnet
EGC_NETWORK_MODE = os.environ.get('EGC_NETWORK_MODE', 'preview').lower()

# Are we running the code in a context where we want wallets to be logged and
# swept after tests to recover collateral etc?
# Options are 'scripted' or 'manual'. If scripted, we log + sweep.
EGC_WALLET_MODE = os.environ.get('EGC_WALLET_MODE', 'manual').lower()

# The default place to save wallets, and log to wallets.log if scripted
# wallet mode.
# TODO better default place for it?
EGC_WALLET_DIR = Path(os.environ.get('EGC_WALLET_DIR', 'keys'))
