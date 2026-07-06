import hashlib
from quart import Blueprint, render_template, request, current_app
from typing import Optional

from egc import *
import logging

LOG = logging.getLogger('egc.webui.blueprints.history')

bp = Blueprint("history", __name__, template_folder="templates")


### index ###


@bp.route("/")
async def index():
    return await render_template("index.html")

def version_including_filter(sub_version: str, filter_str: Optional[str]):
    if filter_str:
        filter_version = hashlib.md5(filter_str.encode()).hexdigest()[:8]
        return f'{filter_version}:{sub_version}'
    else:
        return sub_version


### tree ###


def phase_key(p: ElectionPhase | str) -> tuple[int, ...]:
    match p:
        case ElectionConfigPhase(phase=p2) if p2 is not None:
            return (p.CONSTR_ID, p2.CONSTR_ID)
        case ElectionResultsPhase(phase=p2) if p2 is not None:
            return (p.CONSTR_ID, p2.CONSTR_ID)
        # TODO codify these properly
        case 'ElectionNotStarted':
            return (-1,)
        case 'ElectionEnded':
            return (ElectionFinalizePhase.CONSTR_ID + 1,)
        case _:
            return (p.CONSTR_ID,)


# Gotcha: because we can't construct a value of for example ElectionConfigPhase
# without a concrete sub-phase, we take a hardcoded node_key but look up the
# key for the current_phase.
# TODO need to adjust math here?
def node_phase_class(node_phase_key, phase):
    b = phase_key(phase)
    depth = len(node_phase_key)
    a, b = node_phase_key, b[:depth]        # compare at the node's granularity
    return "phase-past" if a < b else "phase-present" if a == b else "phase-future"


# Makes sure we can't forget structural parts of a build tree node dict
def build_node(id, type, children=None, **fields):
    return {"id": id, "type": type, "children": children or [], **fields}


### other nodes ###

def build_records_node(id_, records, filter_str=None):
    return build_node(
        id = id_,
        type = 'records',
        records = records,
        children = [],
    )

def build_channels_node(id_, channels, filter_str=None):
    return build_node(
        id = id_,
        type = 'channels',
        channels = channels,
        children = [],
    )

def build_ballots_node(id_, title, records, filter_str=None):
    return build_node(
        id = id_,
        type = 'simple',
        title = title,
        children = [
            build_records_node(id_ + '-records', records, filter_str),
        ],
    )



### phase nodes ###

def build_configannouncephase(phase, records=[], filter_str=None):
    node_phase_key = (ElectionConfigPhase.CONSTR_ID, ConfigAnnouncePhase.CONSTR_ID)
    announce_records = [
        r for r in records
        if isinstance(r.metadata, Manifest)
        or isinstance(r.metadata, CeremonyDetails)
    ]
    return build_node(
        id = 'configannouncephase',
        type = 'phase',
        phase_class = node_phase_class(node_phase_key, phase),
        title = 'Announce',
        children = [
            build_records_node('announce-records', announce_records, filter_str)
        ],
    )

def build_configonboardingphase(phase, channels=[], filter_str=None):
    node_phase_key = (ElectionConfigPhase.CONSTR_ID, ConfigOnboardingPhase.CONSTR_ID)
    return build_node(
        id = 'configonboardingphase',
        type = 'phase',
        title = 'Onboarding',
        phase_class = node_phase_class(node_phase_key, phase),
        children = [
            build_channels_node('onboarding-channels', channels, filter_str)
        ],
    )

def build_configceremonyphase(phase, records=[], filter_str=None):
    node_phase_key = (ElectionConfigPhase.CONSTR_ID, ConfigCeremonyPhase.CONSTR_ID)
    ceremony_records = [
        r for r in records
        if isinstance(r.metadata, GuardianPubkey)
        or isinstance(r.metadata, GuardianBackup)
        or isinstance(r.metadata, GuardianVerification)
    ]
    return build_node(
        id = 'configceremonyphase',
        type = 'phase',
        title = 'Key Ceremony',
        phase_class = node_phase_class(node_phase_key, phase),
        children = [
            build_records_node('ceremony-records', ceremony_records, filter_str)
        ],
    )

def build_configfinalizephase(phase, records=[], filter_str=None):
    node_phase_key = (ElectionConfigPhase.CONSTR_ID, ConfigFinalizePhase.CONSTR_ID)
    finalize_records = [
        r for r in records
        if isinstance(r.metadata, JointKey)
        or isinstance(r.metadata, Constants)
        or isinstance(r.metadata, Context)
    ]
    return build_node(
        id = 'configfinalizephase',
        type = 'phase',
        title = 'Finalize', # TODO OK to duplicate?
        phase_class = node_phase_class(node_phase_key, phase),
        children = [
            build_records_node('configfinalize-records', finalize_records, filter_str)
        ],
    )

def build_configphase(phase, records=[], channels=[], filter_str=None):
    node_phase_key = (ElectionConfigPhase.CONSTR_ID,)
    return build_node(
        id = 'configphase',
        type = 'phase',
        title = 'Config',
        phase_class = node_phase_class(node_phase_key, phase),
        children = [
            build_configannouncephase(phase, records, filter_str),
            build_configonboardingphase(phase, channels, filter_str),
            build_configceremonyphase(phase, records, filter_str),
            build_configfinalizephase(phase, records, filter_str),
        ],
    )

def build_votingphase(phase, records=[], filter_str=None):
    node_phase_key = (ElectionVotingPhase.CONSTR_ID,)
    submitted = [r for r in records if isinstance(r.metadata, BallotSubmitted)]
    cast      = [r for r in records if isinstance(r.metadata, CastNotice)]
    spoiled   = [r for r in records if isinstance(r.metadata, BallotSpoiled)]
    cast_ids    = set(r.metadata.ballot_id for r in cast)
    spoiled_ids = set(r.metadata.ballot_id for r in spoiled)
    pending = [
        r for r in submitted
        if  not r.metadata.ballot_id in cast_ids
        and not r.metadata.ballot_id in spoiled_ids
    ]
    return build_node(
        id = 'votingphase',
        type = 'phase',
        title = 'Voting',
        phase_class = node_phase_class(node_phase_key, phase),
        children = [
            build_ballots_node('ballots-submitted', 'Submitted', submitted, filter_str),
            build_ballots_node('ballots-cast'     , 'Cast'     , cast     , filter_str),
            build_ballots_node('ballots-spoiled'  , 'Spoiled'  , spoiled  , filter_str),
            build_ballots_node('ballots-pending'  , 'Pending'  , pending  , filter_str),
        ],
    )

def build_verifyphase(phase, records=[], filter_str=None):
    node_phase_key = (ElectionVerifyPhase.CONSTR_ID,)
    return build_node(
        id = 'verifyphase',
        type = 'phase',
        title = 'Verification',
        phase_class = node_phase_class(node_phase_key, phase),
        children = [],
    )

def build_finalizephase(phase, records=[], filter_str=None):
    node_phase_key = (ElectionFinalizePhase.CONSTR_ID,)
    return build_node(
        id = 'finalizephase',
        type = 'phase',
        title = 'Finalize', # TODO OK to duplicate?
        phase_class = node_phase_class(node_phase_key, phase),
        children = [],
    )

def build_resultstallyphase(phase, records=[], filter_str=None):
    node_phase_key = (ElectionResultsPhase.CONSTR_ID, ResultsTallyPhase.CONSTR_ID)
    return build_node(
        id = 'resultstallyphase',
        type = 'phase',
        title = 'Encrypted Tally',
        phase_class = node_phase_class(node_phase_key, phase),
        children = [],
    )

def build_resultsdecryptphase(phase, records=[], filter_str=None):
    node_phase_key = (ElectionResultsPhase.CONSTR_ID, ResultsDecryptPhase.CONSTR_ID)
    return build_node(
        id = 'resultsdecryptphase',
        type = 'phase',
        title = 'Decrypt',
        phase_class = node_phase_class(node_phase_key, phase),
        children = [],
    )

def build_resultsphase(phase, records=[], filter_str=None):
    node_phase_key = (ElectionResultsPhase.CONSTR_ID,)
    return build_node(
        id = 'resultsphase',
        type = 'phase',
        title = 'Results',
        phase_class = node_phase_class(node_phase_key, phase),
        children = [
            build_resultstallyphase(phase, records, filter_str),
            build_resultsdecryptphase(phase, records, filter_str),
        ],
    )


### tree again ###


def build_tree(phase, records=[], channels=[], filter_str=None):
    # TODO add an empty root template just to avoid this being weird in node.html?
    return {
        'id': 'node-root', 'type': 'root', 'children': [
            build_configphase(phase, records, channels, filter_str),
            build_votingphase(phase, records, filter_str),
            build_resultsphase(phase, records, filter_str),
            build_verifyphase(phase, records, filter_str),
            build_finalizephase(phase, records, filter_str),
        ]
    }

def get_history_filter() -> Optional[str]:
    return request.args.get("filter", "").strip() or None

def get_open_ids() -> set[str]:
    ids = set(filter(None, request.args.get("open", "").split(",")))
    LOG.info(f'open_ids: {ids}')
    return ids

def get_closed_ids() -> set[str]:
    ids = set(filter(None, request.args.get("closed", "").split(",")))
    LOG.info(f'closed_ids: {ids}')
    return ids

def node_matches(node, f):
    return f is None or f.lower() in str(node).lower()

def visible(node, f):
    if f is None:
        return True
    return node_matches(node, f) or any(visible(c, f) for c in node["children"])

def has_visible_child(node, f):
    return any(visible(c, f) for c in node["children"])

def is_open(node, open_ids, closed_ids, f):
    if node["id"] in closed_ids:
        return False                      # explicit user collapse always wins
    if f is not None and has_visible_child(node, f):
        return True                       # filter force-open
    if node["id"] in open_ids:
        return True
    return 'phase_class' in node and node['phase_class'] == 'phase-present'

def toggle_ids(open_ids, closed_ids, node_id, currently_open):
    o, c = set(open_ids), set(closed_ids)
    if currently_open:                    # user is collapsing it
        o.discard(node_id); c.add(node_id)
    else:                                 # user is expanding it
        c.discard(node_id); o.add(node_id)
    return ",".join(sorted(o)), ",".join(sorted(c))


@bp.before_app_serving
async def register_globals():
    current_app.jinja_env.globals.update(
        visible=visible, is_open=is_open, toggle_ids=toggle_ids,
    )


# This isn't technically needed, but helps with debugging.
@bp.route("/tree")
async def tree():
    filter_str = get_history_filter()
    open_ids   = get_open_ids()
    closed_ids = get_closed_ids()
    phase    = current_app.subscriber.current_phase()
    records  = current_app.subscriber.all_records()
    channels = [channel_id_to_string(c) for c in current_app.subscriber.all_channel_ids()]
    LOG.debug(f'channels: {channels}')
    # If loading the tree as a standalone page (for debugging),
    # need to add the HTMX script to it.
    template = (
        "history/partials/tree.html" if request.headers.get("HX-Request")
        else "history/tree_page.html"
    )
    return await render_template(
        template,
        tree=build_tree(phase, records, channels, filter_str),
        open_ids=open_ids, closed_ids=closed_ids,
        filter_str=filter_str,
    )


### filter_results ###


# Because we want to filter both the log and tree at once, we return the two
# divs wrapped in filter_result. Then each is swapped with its correct div
# client side using hx-swap-oob.
# TODO rename something like events? if it's also rendering by polling for changes
@bp.get("/filter")
async def filter_results():
    filter_str = get_history_filter()
    open_ids   = get_open_ids()
    closed_ids = get_closed_ids()

    # return 204 (no new content) if polling and the version hasn't changed
    req_ver = request.headers.get("HX-Trigger-Version")
    cur_ver = version_including_filter(current_app.subscriber.version(), filter_str)
    if cur_ver == req_ver:
        return "", 204 # unchanged; htmx skips the swap

    events   = current_app.subscriber.all_election_events()
    records  = current_app.subscriber.all_records()
    phase    = current_app.subscriber.current_phase()
    channels = [channel_id_to_string(c) for c in current_app.subscriber.all_channel_ids()]

    if filter_str:
        events = [e for e in events if filter_str.lower() in str(e).lower()]

    return await render_template(
        "history/partials/filter_results.html",
        events=events,
        tree=build_tree(phase, records, channels, filter_str),
        open_ids=open_ids, closed_ids=closed_ids,
        filter_str=filter_str, history_ver=cur_ver,
    )
