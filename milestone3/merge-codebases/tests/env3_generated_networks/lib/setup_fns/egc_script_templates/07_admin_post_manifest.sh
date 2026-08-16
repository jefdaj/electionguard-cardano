{% extends "06_admin_post_ipfs.sh" %}
{% block body %}
{{ super() }}
# post first public record as a batch of one
# extra checks to make sure records list works
egc manifest create --manifest-load-json private/manifest.json
find private/records_* -type f
egc records list
egc records post
time timeout 900s egc records await
find private/records_* -type f
egc records list

# prevent the case where admin can burn test tokens and shut down before
# subchannel nodes have fetched records
sleep 30
{% endblock %}
