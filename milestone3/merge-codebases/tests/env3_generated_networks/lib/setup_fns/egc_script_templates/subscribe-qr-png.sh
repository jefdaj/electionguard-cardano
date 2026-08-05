{% include "node-ready.sh" %}

await_file() {
  timeout 600 bash -c 'until [ -e "$1" ]; do sleep 1; done' _ "$1"
  sync    # TODO does this help?
  sleep 3 # TODO does this help?
}

# subscribe to an old election test
QR_PATH='qrcodes/election.png'
await_file "$QR_PATH"
egc election subscribe --election-load-png "$QR_PATH"
egc election events
