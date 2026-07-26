#!/bin/bash

{% block setup %}
export EGC_NODE_NAME={{node_name}}
export EGC_NODE_ROLE={{node_role}}
export EGC_NODE_INDEX={{node_index}}

# makes it easier to load and save files
cd /data

set -Eeuo pipefail
{% if debug_script %}
PS4='+ $(date "+%H:%M:%S") '
set -x
{% endif %}
{% endblock %}

{% block cleanup %}
cleanup() {
  echo "cleaning up"
  # TODO if admin, burn test tokens if any
  # TODO return collateral
}
{% endblock %}

{% block onexit %}
# run cleanup before exiting
export -f cleanup
on_exit() {
  local return_code=$?
  trap - EXIT INT TERM
  set +e
  cleanup & local cleanup_pid=$!
  # 10min timeout to burn tokens + recover collateral
  (sleep 600; kill -KILL "$cleanup_pid" 2>/dev/null) & local watchdog_pid=$!
  wait "$cleanup_pid" || echo "cleanup failed" >&2
  kill "$watchdog_pid" 2>/dev/null
  wait "$watchdog_pid" 2>/dev/null
  exit $return_code
}
trap on_exit EXIT INT TERM
{% endblock %}
{% block body %}
{% endblock %}
