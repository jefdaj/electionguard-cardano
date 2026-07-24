#!/bin/bash

# role: {{role}}
# template: {{template_name}}
# debug: {{debug}}

{% if debug -%}
set -x
{%- endif %}

# TODO set self-identified node name here?

# Make sure Cardano node syncs to 100% and IPFS finds peers
while true; do
  egc node await && break || sleep 5
done

echo "node is ready:"; egc node status | jq
