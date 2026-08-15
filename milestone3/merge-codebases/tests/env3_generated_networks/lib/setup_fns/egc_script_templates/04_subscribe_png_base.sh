{% extends "03_node_ready.sh" %}
{% block cleanup %}
cleanup() {
  echo "cleaning up"
  egc collateral return || true
  # egc records await || true # TODO need a different version with this?
}
{% endblock %}
{% block body %}
{{ super() }}

await_file() {
  timeout 600 bash -c 'until [ -e "$1" ]; do sleep 1; done' _ "$1"
}

# subscribe to an election by qr code
QR_PATH='qrcodes/election.png'
await_file "$QR_PATH"
egc election subscribe --election-load-png "$QR_PATH"
{% endblock %}
