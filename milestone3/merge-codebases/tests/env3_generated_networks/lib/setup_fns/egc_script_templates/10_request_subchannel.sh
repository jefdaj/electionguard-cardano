{% extends "04_subscribe_png.sh" %}

{% block body %}
{{ super() }}
# Request a channel from admin via qrcode.
egc channel request \
  --request-save-png qrcodes/channel-${EGC_NODE_NAME}.png \
  --role $EGC_NODE_ROLE

# Wait to be authorized to post. Normally you wouldn't expect a particular
# index here, but for the tests we want to make sure they line up with the
# docker names etc.
CH_STR=$(egc channel await --role $EGC_NODE_ROLE)
{% endblock %}

{% block cleanup %}
egc collateral return
{% endblock %}

{% block report %}
egc election events
[[ $CH_STR == $EGC_NODE_NAME ]] && echo "correct channel" || echo "wrong channel"
{% endblock %}
