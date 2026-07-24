#!/bin/bash

{% block setup %}
### setup ###

{% if debug_script %}
PS4='+ $(date "+%H:%M:%S") '
set -x
{% endif %}
export EGC_NODE_NAME={{node_name}}
export EGC_NODE_ROLE={{node_role}}
export EGC_NODE_INDEX={{node_index}}
{% endblock %}

{% block cleanup %}
cleanup() {
  echo "cleaning up"
  # TODO if admin, burn test tokens if any
  # TODO return collateral
}
{% endblock %}

{% block onexit %}
### run cleanup on exit ###

export -f cleanup
on_exit() {
  local return_code=$?
  trap - EXIT INT TERM
  cleanup & local cleanup_pid=$!
  (sleep 600; kill -KILL "$cleanup_pid" 2>/dev/null) & local watchdog_pid=$!
  wait "$cleanup_pid" || echo "cleanup failed" >&2
  kill "$watchdog_pid" 2>/dev/null
  wait "$watchdog_pid" 2>/dev/null
  exit $return_code
}
trap on_exit EXIT INT TERM
{% endblock %}

{% block body %}
### body ###
{% endblock %}
