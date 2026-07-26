{% include "node-ready.sh" %}

# subscribe to an old election test
egc election subscribe --parse-str "$(cat qrcodes/election.txt)"
egc election events
