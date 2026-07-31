{% extends "base.sh" %}

{% block body %}
{{ super() }}
egc wallet create --description admin

egc election create --funder-load-json private/funder.sk --admin-ada 200

# TODO write share()
egc election share --election-save-png qrcodes/election.png

# TODO await admin channel

# TODO factor out a template once working:
# TODO burn test tokens
# TODO return collateral
{% endblock %}
