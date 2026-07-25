{% include "node-ready.sh" %}

# subscribe to an old election test
egc election subscribe --parse-str "$(cat qr-str.txt)"
egc election events
