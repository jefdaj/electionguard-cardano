{% extends "06_sub_show_ipfs.sh" %}
{% block body %}
{{ super() }}
# check that records were fetched
egc records await
find private/records_* -type f
{% endblock %}
