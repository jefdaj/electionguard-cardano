import ipaddress
import aioipfs
import logging


LOG = logging.getLogger(__name__)


# ---- multiaddr helpers -------------------------------------------------

def _parse(ma):
    """Turn '/ip4/1.2.3.4/tcp/4001/p2p/Qm...' into {'ip4': '1.2.3.4', ...}."""
    parts = ma.strip("/").split("/")
    return dict(zip(parts[0::2], parts[1::2]))


def _ip(d):
    raw = d.get("ip4") or d.get("ip6")
    try:
        return ipaddress.ip_address(raw) if raw else None
    except ValueError:
        return None


def _is_circuit(ma):
    return "/p2p-circuit" in ma


def _keep(ma, lan):
    """Decide whether a (direct) multiaddr is a useful hint for the scope."""
    d = _parse(ma)
    ip = _ip(d)

    # DNS-based addrs (dnsaddr/dns4/dns6) are global, name-resolved endpoints.
    if any(k in d for k in ("dnsaddr", "dns4", "dns6")):
        return not lan

    if ip is None:
        return False
    if ip.is_loopback or ip.is_unspecified or ip.is_multicast or ip.is_link_local:
        return False

    return ip.is_private if lan else ip.is_global


def _rank(ma, lan):
    """Lower sorts first. Prefer QUIC, then the scope we asked for, then TCP."""
    d = _parse(ma)
    ip = _ip(d)
    quic = 0 if "quic-v1" in ma or "quic" in ma else 1
    scope = 0 if (ip and (ip.is_private if lan else ip.is_global)) else 1
    tcp = 0 if "tcp" in d else 1
    return (scope, quic, tcp)


def _strip_own(ma, my_id):
    """Drop only the terminal '/p2p/<my_id>', preserving the rest verbatim."""
    suffix = f"/p2p/{my_id}"
    return ma[:-len(suffix)] if ma.endswith(suffix) else ma


# ---- main --------------------------------------------------------------

async def make_addr_hints(client, n_hints=4, prefer_lan=False,
                          want_peers=(), include_relays=None):
    """
    Build a short, prioritized list of multiaddr hints to hand to peers.

    client         : aioipfs.AsyncIPFS
    n_hints        : max number of hints to return
    prefer_lan     : True -> favor LAN reachability, False -> favor global
    want_peers     : peer ids you want to be dialable by (biases the hint
                     ordering toward address families already seen working)
    include_relays : None -> auto (relays only in global mode)
                     True  -> always include, False -> never include

    Relay hints are emitted as compact 'r:'-prefixed tokens and must be
    passed through expand_addr_hints() on the read end before dialing.
    """
    me = await client.core.id()
    my_id = me["ID"]
    LOG.debug(f'my_id: {my_id}')
    candidates = set(me.get("Addresses") or [])
    LOG.debug(f'candidates: {candidates}')

    if include_relays is None:
        include_relays = not prefer_lan  # relays only help global reachability

    # --- learn which local families actually work with wanted peers ---
    seen_families = set()
    if want_peers:
        want = set(want_peers)
        for p in (await client.swarm.peers()).get("Peers") or []:
            if p.get("Peer") in want:
                d = _parse(p.get("Addr", ""))
                seen_families.add("ip6" if "ip6" in d else "ip4")
    LOG.debug(f'seen_families: {seen_families}')

    # --- direct hints: filter to scope, strip our own /p2p suffix ---
    direct = {
        _strip_own(a, my_id)
        for a in candidates
        if not _is_circuit(a) and _keep(a, prefer_lan)
    }
    LOG.debug(f'direct: {direct}')

    def sort_key(ma):
        d = _parse(ma)
        fam = "ip6" if "ip6" in d else "ip4"
        return (0 if fam in seen_families else 1, *_rank(ma, prefer_lan))

    ordered = sorted(direct, key=sort_key)
    LOG.debug(f'ordered: {ordered}')

    # --- compact relay tokens (publish minimal, expand on read) ---
    relays = []
    if include_relays:
        for a in candidates:
            if not _is_circuit(a):
                continue
            # Keep everything up to '/p2p-circuit' and drop the trailing
            # '/p2p/<my_id>', then tag it as a relay with the 'r:' prefix.
            #
            # Full relay address (used here) keeps the relay's transport,
            # so no DHT lookup is needed on the read end, e.g.:
            #   r:/ip4/198.51.100.7/tcp/4001/p2p/QmRelay
            #
            # Shorter variant for later: publish only the relay's peer id
            # and let the reader's node resolve it via the DHT. Take the
            # part before '/p2p-circuit' and keep its trailing '/p2p/<relay>':
            #   relay_id = a.split("/p2p-circuit")[0].rsplit("/p2p/", 1)[1]
            #   token = f"r:/p2p/{relay_id}"
            token = "r:" + a.split("/p2p-circuit")[0].rstrip("/")
            relays.append(token)
        relays = sorted(set(relays))
    LOG.debug(f'relays: {relays}')

    # direct hints take priority; relays fill remaining slots as fallback
    hints = ordered[:n_hints]
    if include_relays:
        for r in relays:
            if len(hints) >= n_hints:
                break
            if r not in hints:
                hints.append(r)
    LOG.debug(f'hints: {hints}')
    return hints


# ---- read-end expander -------------------------------------------------

def expand_addr_hints(peer_id, hints):
    """
    Rebuild dialable multiaddrs from published hints for a given peer id.

    Direct hints  -> '<hint>/p2p/<peer_id>'
    Relay tokens  -> '<relay-addr>/p2p-circuit/p2p/<peer_id>'
                     (identified unambiguously by the 'r:' prefix)
    """
    out = []
    for h in hints:
        if h.startswith("r:"):
            relay = h[2:]
            out.append(f"{relay}/p2p-circuit/p2p/{peer_id}")
        else:
            out.append(f"{h}/p2p/{peer_id}")
    return out
