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

{% block exittrap %}
### exit trap ###
# TODO if admin, burn test tokens if any
# TODO return collateral
{% endblock %}

{% block body %}
### body ###
{% endblock %}
