{% extends "base.sh" %}

{% block body %}
{{ super() }}
egc wallet create --description 'admin wallet (created as observer)'
egc wallet show

# TODO init election (separate funder key)

# TODO await admin channel

# TODO factor out a template once working:
# TODO burn test tokens
# TODO return collateral
{% endblock %}
