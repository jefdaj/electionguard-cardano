{% extends "06_admin_ipfs.sh" %}
{% block body %}
{{ super() }}
# first proper batch: 2 records and advance phase
egc ceremony create --ceremony-load-json private/ceremony.json
egc manifest create --manifest-load-json private/manifest.json
find private/records_* -type f
egc records list
egc records post --advance-phase config_onboarding
egc records await
find private/records_* -type f
egc records list
{% endblock %}
