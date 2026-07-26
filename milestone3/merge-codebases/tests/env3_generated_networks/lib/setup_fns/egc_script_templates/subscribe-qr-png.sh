{% include "node-ready.sh" %}

# subscribe to an old election test
egc election subscribe --election-load-png qrcodes/election.png
egc election events
