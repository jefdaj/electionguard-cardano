{% extends "subscribe-qr-png-base.sh" %}
{% block body %}
{{ super() }}

# Request a channel from admin via qrcode.
egc channel request \
  --role $EGC_NODE_ROLE \
  --request-save-png qrcodes/channel-${EGC_NODE_NAME}.png

# Wait to be authorized to post. Normally you wouldn't expect any particular
# index here, but for the tests we want to make sure they line up with the
# docker names etc.
CH_STR=$(egc channel await --role $EGC_NODE_ROLE)
[[ $CH_STR == $EGC_NODE_NAME ]] || (echo "wrong channel"; exit 1)
{% endblock %}
