{% extends "06_admin_post_ipfs.sh" %}
{% block body %}
{{ super() }}
# post first public record as a batch of one
# extra checks to make sure records list works
egc manifest create --manifest-load-json private/manifest.json
find private/records_* -type f
egc records list
egc records post
egc records await
find private/records_* -type f
egc records list
{% endblock %}
