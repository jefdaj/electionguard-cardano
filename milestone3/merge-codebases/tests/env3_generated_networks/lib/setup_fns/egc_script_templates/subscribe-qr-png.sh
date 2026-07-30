{% include "node-ready.sh" %}

await_file() {
  export path="$1"
  timeout 300 bash -c 'until [ -e "$path" ]; do sleep 1; done'
}

# subscribe to an old election test
QR_PATH='qrcodes/election.png'
await_file "$QR_PATH"
egc election subscribe --election-load-png "$QR_PATH"
egc election events
