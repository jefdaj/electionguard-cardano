{% extends "06_admin_post_ipfs.sh" %}

{% block body %}
{{ super() }}
# first proper batch: post 2 records and advance phase
egc manifest create --manifest-load-json private/manifest.json
egc ceremony create --ceremony-load-json private/ceremony.json
egc records list
egc records post --advance-phase config_onboarding
egc records await # should be immediate
{% endblock %}

{% block report %}
egc election events
find private/records_* -type f
egc records list
{% endblock %}
