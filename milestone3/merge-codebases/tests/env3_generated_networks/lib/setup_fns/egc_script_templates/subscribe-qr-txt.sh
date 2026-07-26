{% include "node-ready.sh" %}

# subscribe to an old election test
egc election subscribe --election-load-txt qrcodes/election.txt
egc election events
