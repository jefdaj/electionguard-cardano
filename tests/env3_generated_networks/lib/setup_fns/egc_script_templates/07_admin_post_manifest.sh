{% extends "06_admin_post_ipfs.sh" %}
{% block body %}
{{ super() }}
# post first public record as a batch of one
# extra checks to make sure records list works
egc manifest create --manifest-load-json private/manifest.json
egc records list
egc records post
egc records await # should be immediate from the same ipfs node
{% endblock %}

{% block report %}
egc election events
find private/records_* -type f
egc records list
{% endblock %}
