{% extends "base.sh" %}

{% block cleanup %}
cleanup() {
  echo "cleaning up"
  egc election burntesttokens || true # TODO true not needed?
  # TODO return collateral
}
{% endblock %}

{% block body %}
{{ super() }}
egc wallet create --description admin
egc election create --funder-load-json private/funder.sk --admin-ada 200
egc election share --election-save-png qrcodes/election.png
# TODO await admin channel
egc election events
{% endblock %}
