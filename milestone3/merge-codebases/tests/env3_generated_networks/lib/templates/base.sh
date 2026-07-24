#!/bin/bash

{% block setup %}
### setup ###
{% if debug_script %}
set -x
{% endif %}
export EGC_NODE_NAME='{{node_name}}'
export EGC_NODE_ROLE='{{node_role}}'
export EGC_NODE_INDEX='{{node_index}}'
{% endblock %}

{% block cleanup %}
cleanup() {
  # TODO if admin, burn test tokens if any
  # TODO return collateral
  echo "cleaning up"
}
{% endblock %}

{% block exittrap %}
### run cleanup ###
export -f cleanup
on_exit() {
  local return_code=$?
  trap - EXIT INT TERM
  timeout -k 10s 600s bash -c cleanup || echo "cleanup failed or timed out"
  exit $return_code
}
trap on_exit EXIT INT TERM
{% endblock %}

{% block body %}
### body ###
{% endblock %}
