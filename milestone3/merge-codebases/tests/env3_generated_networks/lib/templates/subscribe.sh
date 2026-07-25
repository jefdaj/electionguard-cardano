{% include "node-ready.sh" %}

# subscribe to an old election test
egc election subscribe --parse-str "$(cat qr-str.txt)"

# TODO events once there are any
# egc phase await 'EgcPhase.CONFIG_ANNOUNCE' # TODO what should this look like
