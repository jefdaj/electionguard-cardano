{% include "node-ready.sh" %}

await_file() {
  timeout 300 bash -c 'until [ -e "$1" ]; do sleep 1; done' _ "$1"
  sleep 3 # TODO how long is needed?
}

# subscribe to an old election test
QR_PATH='qrcodes/election.png'
await_file "$QR_PATH"
egc election subscribe --election-load-png "$QR_PATH"
egc election events
