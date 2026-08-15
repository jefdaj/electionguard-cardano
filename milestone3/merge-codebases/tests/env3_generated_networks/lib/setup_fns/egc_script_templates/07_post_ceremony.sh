{% extends "06_admin_ipfs.sh" %}
{% block body %}
{{ super() }}
# post first public record as a batch of one
# TODO manifest here instead?
egc ceremony create --ceremony-load-json private/ceremony.json
find private/records_* -type f
egc records list
egc records post
egc records await
find private/records_* -type f
egc records list
{% endblock %}
