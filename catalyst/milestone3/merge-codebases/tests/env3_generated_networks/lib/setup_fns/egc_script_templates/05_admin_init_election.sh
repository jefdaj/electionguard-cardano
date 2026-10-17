{% extends "03_node_ready.sh" %}

{% block body %}
{{ super() }}
# This will be used for the number of qrcodes to expect later,
# and right away to estimate admin ada.
N_SUBS=$(< private/n_subs.txt)

# create an election using separate dev wallet as funder
# TODO more realistic formula for ADA needed including n votes, guardians, etc
ADA_PER_SUB=20
ADMIN_ADA=$(( 100 + 5*N_SUBS + ADA_PER_SUB*N_SUBS ))
egc election create --funder-load-json private/funder.sk --admin-ada $ADMIN_ADA
egc election share --election-save-png qrcodes/election.png

# become the admin of the new election
egc collateral await
CH_STR=$(egc channel await --role admin)
{% endblock %}

{% block cleanup %}
egc election burntesttokens
egc collateral return
egc records await
{% endblock %}

{% block report %}
[[ "$CH_STR" == "admin" ]] || { echo "failed to acquire admin channel" >&2; exit 1; }
egc election events
{% endblock %}
