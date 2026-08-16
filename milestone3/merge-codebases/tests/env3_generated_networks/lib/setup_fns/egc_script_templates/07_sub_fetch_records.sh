{% extends "04_subscribe_png.sh" %}
{% block cleanup %}
cleanup() {
  # check that records were fetched
  time timeout 900s egc records await
  find private/records_* -type f
  echo "cleaning up";
}
{% endblock %}
{% block body %}
{{ super() }}
egc election events
{% endblock %}
