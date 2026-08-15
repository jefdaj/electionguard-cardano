{% extends "06_sub_show_ipfs.sh" %}
{% block cleanup %}
cleanup() {
  egc election events
  # check that records were fetched
  egc records await
  find private/records_* -type f
  echo "cleaning up";
}
{% endblock %}
