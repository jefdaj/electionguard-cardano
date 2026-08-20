#!/bin/bash

{% block setup %}
export EGC_NODE_NAME={{node_name}}
export EGC_NODE_ROLE={{node_role}}
export EGC_NODE_INDEX={{node_index}}

# makes it easier to load and save files
cd /data

set -Eeuo pipefail
{% if debug_script %}
PS4='+ {{node_name}} $(date "+%H:%M:%S") '
set -x
{% endif %}
{% endblock %}

cleanup() {
{% block cleanup %}
echo "cleanup here"
{% endblock %}
}

report() {
{% block report %}
echo "report here"
{% endblock %}
}

{% block onexit %}
# run cleanup + report before exiting
export -f cleanup
export -f report
on_exit() {
  local return_code=$?
  trap - EXIT INT TERM
  set +e
  cleanup & local cleanup_pid=$!
  # long timeout to burn tokens, recover collateral, fetch files, etc
  (sleep 1200; kill -KILL "$cleanup_pid" 2>/dev/null) & local watchdog_pid=$!
  wait "$cleanup_pid" || echo "cleanup failed" >&2
  kill "$watchdog_pid" 2>/dev/null
  wait "$watchdog_pid" 2>/dev/null
  report # TODO timeout?
  exit $return_code
}
trap on_exit EXIT INT TERM
{% endblock -%}

{% block body %}
{% endblock %}
