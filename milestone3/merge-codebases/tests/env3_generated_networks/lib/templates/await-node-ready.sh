#!/usr/bin/env bash

# role: {{role}}
# debug: {{debug}}
# template: {{template_name}}

# TODO set self-identified node name first?
# TODO env var for logfile? i guess during node run

{% if debug %}
set -x
{% endif %}

# Make sure Cardano node syncs to 100% and IPFS finds peers
while true; do
  egc node await && echo "node is ready" && break || sleep 5
done
