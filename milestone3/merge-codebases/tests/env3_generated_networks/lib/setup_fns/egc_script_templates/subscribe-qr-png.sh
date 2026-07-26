{% include "node-ready.sh" %}

# subscribe to an old election test
egc election subscribe --election-load-qr qrcodes/election.png
egc election events
