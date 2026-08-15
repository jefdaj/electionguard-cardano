{% extends "03_node_ready.sh" %}
{% block cleanup %}
cleanup() {
  egc election events
  echo "cleaning up";
}
{% endblock %}
{% block body %}
{{ super() }}

await_file() {
  timeout 900 bash -c 'until [ -e "$1" ]; do sleep 1; done' _ "$1"
}

# subscribe to election via qr code
QR_PATH='qrcodes/election.png'
await_file "$QR_PATH"
egc election subscribe --election-load-png "$QR_PATH"
{% endblock %}
