import aiofiles
import asyncio
import os
import random
import tempfile
import threading
import time
import hashlib
import shutil

from aiohttp import ClientConnectorError, ClientConnectorDNSError
from aioipfs import AsyncIPFS

from .plutus  import *
from .records import *

from .ipfs_hints import make_addr_hints, expand_addr_hints

import logging

LOG = logging.getLogger(__name__)


IPFS_API_ADDR = os.environ.get('IPFS_API_ADDR', '/dns4/127.0.0.1/tcp/5001')
LOG.info(f'IPFS_API_ADDR: {IPFS_API_ADDR}')

# Force reconnect to all addr_hints if there have been CIDs pending with no
# data transfer for this many seconds.
IPFS_STUCK_WINDOW = 120


class RetryingIPFS:
    """Thin retrying wrapper: handles CONNECTION-level failures (node
    down/DNS). Content-availability ("CID not here yet") is handled by the
    service lanes.
    """

    def __init__(self, maddr, retries=10, delay=1.0, backoff=1.5):
        self._client  = AsyncIPFS(maddr=maddr)
        self._retries = retries
        self._delay   = delay
        self._backoff = backoff

    async def close(self):
        await self._client.close()

    async def _retry(self, coro_factory):
        delay = self._delay
        for attempt in range(self._retries):
            try:
                return await coro_factory()
            except (ClientConnectorError, ClientConnectorDNSError):
                if attempt == self._retries - 1:
                    raise
                await asyncio.sleep(delay)
                delay *= self._backoff

    async def add(self, *a, **k):
        k.setdefault('cid_version', 1)
        return await self._retry(lambda: self._client.add(*a, **k))

    async def add_json(self, *a, **k):
        k.setdefault('cid_version', 1)
        return await self._retry(lambda: self._client.add_json(*a, **k))

    async def cat(self, *a, **k):
        return await self._retry(lambda: self._client.cat(*a, **k))

    async def get(self, *a, **k):
        return await self._retry(lambda: self._client.get(*a, **k))

    async def pin_add(self, *a, **k):
        return await self._retry(lambda: self._client.pin.add(*a, **k))

    def __getattr__(self, name): # fallback, no retries
        return getattr(self._client, name)


def record_key(record) -> str:
    "Work around record `unhashable type` issues."
    # TODO add a method to the dataclass instead?
    # TODO use entire record including cid for key?
    return str(record.metadata)


class PendingStore:
    """Claude tried to add a SQLite db here. I rewrote it as a dict but left
    the class in case we want persistent storage later.
    """

    def __init__(self):
        self._db = {} # metadata str -> (record, attempts, next attempt)

    def add(self, record):
        key = record_key(record)
        if key in self._db.keys():
            LOG.info(f'add {record} ignoring duplicate')
        else:
            LOG.info(f'add {record}')
            self._db[key] = (record, 0, 0)

    def remove(self, record):
        key = record_key(record)
        # LOG.debug(f'remove {record}')
        del self._db[key]

    def mark_attempt(self, record, attempts, next_attempt):
        key = record_key(record)
        LOG.info(f'mark_attempt record:{record} attempts:{attempts} next_attempt:{next_attempt}')
        self._db[key] = (record, attempts, next_attempt)

    def due(self, now):
        records_due = [
            (record, attempts)
            for (record, attempts, next_attempt) in self._db.values()
            if next_attempt <= now
        ]
        if records_due:
            LOG.debug(f'records_due: {len(records_due)}')
        random.shuffle(records_due) # TODO is this a good strategy? or should they be sorted?
        return records_due

    def count(self):
        return len(self._db.keys())



class PostFetchMismatchError(Exception):
    "One or more fetched paths have different content than their to-post equivalents."

    def __init__(self, mismatches: list[Path]):
        self.mismatches = mismatches
        super().__init__(f"{len(mismatches)} mismatch(es): {mismatches}")


def _hash(path: Path, chunk=64*1024) -> str:
    # TODO any subtle serialization issues here?
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def remove_fetched_from_to_post(records_to_post: Path, records_fetched: Path) -> list[Path]:
    """Delete files in records_to_post that also exist in records_fetched with
    identical content. After processing everything, raise PostFetchMismatchError
    if any shared relative path had differing content. Returns removed rel paths."""
    removed, mismatches = [], []
    for post_file in records_to_post.rglob("*"):
        if not post_file.is_file():
            continue
        rel = post_file.relative_to(records_to_post)
        fetched_file = records_fetched / rel
        if not fetched_file.is_file():
            continue

        if (post_file.stat().st_size == fetched_file.stat().st_size
                and _hash(post_file) == _hash(fetched_file)):
            post_file.unlink()
            removed.append(rel)
        else:
            mismatches.append(rel)
    if mismatches:
        raise PostFetchMismatchError(mismatches)
    return removed


class IPFSService:
    """The service: owns the event loop, both lanes, and the store.
    Each ElectionNode should have one of these and use it for all IPFS calls.
    """

    # TODO tune these defaults based on test data
    def __init__(self,
        records_to_post_dir: Path,
        records_fetched_dir: Path,
        maddr=IPFS_API_ADDR,
        fresh_workers=4,
        fresh_timeout=10,    # short: withheld CIDs fail fast
        retry_timeout=30,    # patient: give real files a chance
        retry_concurrency=4, # bounded => can't hog the node
        sweep_interval=1,    # how often the sweeper wakes
        base_delay=1,        # first retry backoff
        max_delay=30,       # retry-forever settles to every 10 min
        backoff=1.5
    ):

        self.records_to_post_dir = records_to_post_dir
        self.records_fetched_dir = records_fetched_dir

        # These are set by the node's on_channel_event handler.
        self.channel_nodes: dict[ChannelId, OptionIpfsNode] = {}

        self.maddr = maddr
        self.fresh_workers = fresh_workers
        self.fresh_timeout = fresh_timeout
        self.retry_timeout = retry_timeout
        self.sweep_interval = sweep_interval
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff = backoff

        self._retry_concurrency = retry_concurrency

        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._ready = threading.Event()

        self.ipfs = None
        self.store = None
        self._fresh_q = None
        self._retry_sem = None
        self._inflight = set() # CIDs being fetched right now (dedup)

        # For detecting whether data transfers are stuck.
        # (monotonic_time, blocks_sent, blocks_recv) at last meaningful poll
        self._last_bitswap_snapshot: tuple[float, int, int] | None = None


    def _run_loop(self):
        "Lifecycle."
        asyncio.set_event_loop(self._loop)
        self.ipfs = RetryingIPFS(self.maddr)
        self.store = PendingStore()
        self._fresh_q = asyncio.Queue()
        self._retry_sem = asyncio.Semaphore(self._retry_concurrency)
        for _ in range(self.fresh_workers):
            self._loop.create_task(self._fresh_worker())
        self._loop.create_task(self._sweeper())
        self._loop.create_task(self._watchdog())
        self._ready.set()
        self._loop.run_forever()

    def start(self):
        self._thread.start()
        self._ready.wait()

    def stop(self):
        asyncio.run_coroutine_threadsafe(self.ipfs.close(), self._loop).result(10)
        self._loop.call_soon_threadsafe(self._loop.stop)

    def _run_sync(self, coro, timeout: float | None = None):
        "Call an async method from a sync context (a DIFFERENT thread). All calls should go through one of these?"
        fut = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return fut.result(timeout) # blocks, re-raises exceptions here

    async def _run_async(self, coro, timeout=None):
        "Call an async method from for example FastAPI. All calls should go through one of these?"
        fut = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return await asyncio.wait_for(asyncio.wrap_future(fut), timeout)

    def _accept(self, record):
        self.store.add(record)                # persist first
        self._fresh_q.put_nowait((record, 0)) # then attempt promptly

    def fetch_record_soon(self, record: PublicRecord):
        "Called from the subscriber thread. Returns immediately."
        self._loop.call_soon_threadsafe(self._accept, record)

    def publish_and_make_record(self, data: dict, metadata: PublicRecordMetadata) -> PublicRecord:
        "Publish data to IPFS and return a new record, ready to post onchain."
        added_file = self._run_sync(self.ipfs.add_json(data))
        cid_str = added_file['Hash']
        LOG.debug(f'cid_str: {cid_str}')
        cid_bytes = coerce_ipfs_cid(cid_str)
        LOG.debug(f'cid_bytes: {cid_bytes}')
        record = PublicRecord(
            ipfs_cid = cid_bytes,
            metadata = metadata,
        )
        return record

    def publish_and_make_records(
        self,
        pairs: list[tuple[dict, PublicRecordMetadata]],
    ) -> list[PublicRecord]:
        # TODO how should we handle failures partway through here?
        records = []
        for (data, metadata) in pairs:
            record = self.publish_and_make_record(data, metadata)
            LOG.info(f'published {record}')
            records.append(record)
        return records

    async def _attempt_fetch(self, record: PublicRecord, timeout):
        "The one fetch primitive both lanes share."
        key = record_key(record)
        if key in self._inflight: # never fetch same CID twice at once
            return False
        self._inflight.add(key)
        try:
            cid_str = ipfs_cid_to_string(record.ipfs_cid)
            data = await self._run_async(self.ipfs.cat(cid_str), timeout=timeout)
            await self._save_fetched_data(data, record)
            async for pin_status in self.ipfs._client.pin.add(cid_str):
                LOG.debug(f'progress pinning {cid_str}: {pin_status}')
            self.store.remove(record) # success => no longer pending
            remove_fetched_from_to_post(self.records_to_post_dir, self.records_fetched_dir)
            LOG.info("fetched %s", record)
            return True
        except asyncio.TimeoutError:
            return False # file not propagated to ipfs node yet
        except Exception as e:
            LOG.error("fetch error %s: %s", record, e)
            return False # keep it pending, retry later
        finally:
            self._inflight.discard(key)

    async def _fresh_worker(self):
        "Fresh lane: prompt, short timeout, one shot each."
        while True:
            record, _ = await self._fresh_q.get()
            try:
                ok = await self._attempt_fetch(record, self.fresh_timeout)
                if not ok:
                    self._schedule_retry(record, attempts=1) # demote to slow lane
            finally:
                self._fresh_q.task_done()

    def _schedule_retry(self, record, attempts):
        "Jitter to prevent all test nodes retrying at once."
        cap = min(self.base_delay * self.backoff ** (attempts - 1), self.max_delay)
        delay = random.uniform(0, cap) # full jitter
        self.store.mark_attempt(record, attempts, time.time() + delay)


    async def _ipfs_is_reachable(self) -> bool:
        """Lightweight check — returns False if the IPFS node is down."""
        try:
            await self.ipfs._client.version()
            return True
        except Exception:
            return False

    async def _ipfs_is_stuck(self):
        """Check bitswap stats and return True if the node appears stuck.
        Returns True if there are pending wants but no data has moved in the last IPFS_STUCK_WINDOW seconds.
        Updates self._last_bitswap_snapshot on success.
        """
        if not await self._ipfs_is_reachable():
            LOG.warning('ipfs node is unreachable; skipping stuck check')
            return False # not "stuck" in the reconnectable sense — nothing to reconnect to
        try:
            stat = await self.ipfs._client.bitswap.stat()
        except Exception as e:
            LOG.error(f'failed to get bitswap stat; skipping stuck check: {e}')
            return False
        if stat is None:
            LOG.error('bitswap stat returned None; skipping stuck check')
            return False

        LOG.debug(f'stat: {stat}')

        blocks_sent = int(stat.get('BlocksSent',     0))
        blocks_recv = int(stat.get('BlocksReceived', 0))
        n_waiting   = len(stat.get('Wantlist',      []))
        now         = time.monotonic()

        if n_waiting == 0:
            # Nothing pending; update snapshot so the clock resets.
            self._last_bitswap_snapshot = (now, blocks_sent, blocks_recv)
            return False

        # We have pending wants. Check whether any data has moved since
        # the last snapshot.
        if self._last_bitswap_snapshot is None:
            # First poll with a non-empty wantlist; start the clock.
            self._last_bitswap_snapshot = (now, blocks_sent, blocks_recv)
            return False

        snap_time, snap_sent, snap_recv = self._last_bitswap_snapshot

        data_moved = (blocks_sent - snap_sent) + (blocks_recv - snap_recv)
        if data_moved > 0:
            # Progress since last snapshot; reset the clock.
            self._last_bitswap_snapshot = (now, blocks_sent, blocks_recv)
            return False

        # No progress. Are we past the stuck window?
        return (now - snap_time) >= self.IPFS_STUCK_WINDOW

    async def _force_reconnect(self, maddr: str):
        LOG.warning(f'_force_reconnect {maddr}')
        try:
            await self.ipfs._client.swarm.disconnect(maddr)
        except Exception:
            pass
        try:
            await self.ipfs._client.swarm.connect(maddr)
        except Exception:
            pass

    async def _watchdog(self, interval=30, jitter=True):
        """Force reconnect when the node appears stuck (peers connected but no
        data moving). Polls every ~30s; triggers if nothing has transferred for
        IPFS_STUCK_WINDOW seconds while wants are pending."""
        while True:
            if jitter:
                await asyncio.sleep(interval * random.uniform(0.8, 1.2))
            else:
                await asyncio.sleep(interval)
            try:
                stuck = await self._ipfs_is_stuck()
            except Exception as e:
                LOG.error(f'unexpected error in _ipfs_is_stuck: {e}')
                continue
            if not stuck:
                continue
            LOG.error('ipfs is stuck. force reconnecting all addrs...')
            self._last_bitswap_snapshot = None  # reset so we don't re-trigger immediately
            for maddr in self.all_channel_addr_hints():
                task = self._loop.create_task(self._force_reconnect(maddr))
                task.add_done_callback(
                    lambda t: t.exception() and LOG.error(t.exception())
                )


    async def _sweeper(self, jitter=True):
        """Retry lane: patient, bounded, forever, on a slow cadence.
        Jitter to prevent all test nodes sweeping at once.
        """
        while True:
            interval = self.sweep_interval
            if jitter:
                interval *= random.uniform(0.8, 1.2)
            await asyncio.sleep(interval)
            now = time.time()
            for record, attempts in self.store.due(now):
                key = record_key(record)
                if key in self._inflight:
                    continue
                await self._retry_sem.acquire()
                task = self._loop.create_task(self._retry_one(record, attempts))
                task.add_done_callback(
                    lambda t: t.exception() and LOG.error(t.exception())
                )

    async def _retry_one(self, record, attempts):
        try:
            ok = await self._attempt_fetch(record, self.retry_timeout)
            if not ok:
                self._schedule_retry(record, attempts + 1) # cap keeps it periodic
        finally:
            self._retry_sem.release()

    async def _status(self):
        connected = False
        try:
            peers = await self.ipfs._client.swarm.peers()
            peers = peers.get('Peers')
            n_peers = len(peers)
            connected = True
        except Exception as e:
            LOG.error(e)
            n_peers = 0
        try:
            bw = await self.ipfs._client.stats.bw()
            rate = int(bw.get("RateIn", 0) + bw.get("RateOut", 0))
            connected = True
        except Exception as e:
            LOG.error(e)
            rate = 0
        return {
            'connected': connected,
            'n_peers': n_peers,
            'bandwidth_Bs': rate
        }

    async def status(self):
        return await self._run_async(self._status()) # TODO timeout?

    def status_sync(self):
        return self._run_sync(self._status())

    def count_pending_records(self):
        return self.store.count()

    async def wait_until_stable(
        self,
        timeout=300,
        min_peers=3, # TODO why does setting this higher delay stability?
        rate_threshold=50_000, # bytes/sec (RateIn + RateOut)
        required_stable_polls=3,
        interval=5,
    ):
        """Wait until the IPFS node has found some peers and the initial spike
        of bandwidth from searching for them subsides. Needs to be tuned for
        real life performance. Should be changed in sync with ipfs-caps.json.
        """
        end = asyncio.get_event_loop().time() + timeout
        stable = 0
        while True:
            try:
                cur_status = await self.status()
                LOG.debug(f'wait_until_stable {cur_status}')
                n = cur_status['n_peers']
                r = cur_status['bandwidth_Bs']
                if n >= min_peers and r < rate_threshold:
                    stable += 1
                    if stable >= required_stable_polls:
                        return
                else:
                    stable = 0
            except (ClientConnectorError, ClientConnectorDNSError):
                stable = 0 # node not up yet; don't count toward stability
            finally:
                await asyncio.sleep(interval)
            if asyncio.get_event_loop().time() > end:
                raise TimeoutError("IPFS did not stabilize in time")

    def wait_until_stable_sync(self, *args, **kwargs):
        return self._run_sync(self.wait_until_stable(*args, **kwargs))

    async def _save_fetched_data(self, data: bytes, record: PublicRecord):
        """Given a record and bytes matching its CID, write the bytes to the
        proper file. Returns the save path, although that isn't used so far.
        """
        save_path = record_path(
            record.metadata,
            pub_dir = self.records_fetched_dir
        )
        LOG.debug(f'save_path: {save_path}')
        cid_str = ipfs_cid_to_string(record.ipfs_cid)
        LOG.debug(f'cid_str: {cid_str}')
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(suffix=".json.part")
        os.close(fd) # we'll reopen it with aiofiles next
        try:
            # Write tmpfile, then move into place atomically...ish?
            async with aiofiles.open(tmp_path, "wb") as f:
                await f.write(data)
                await f.flush()
            shutil.move(tmp_path, save_path)
            return save_path
        finally:
            # Clean up tmpfile if anything went wrong before replace
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    def get_own_peer_id(self) -> IpfsPeerId:
        LOG.debug('get_own_peer_id')
        id_str = self._run_sync(self.ipfs._client.id())['ID']
        LOG.debug(f'id_str: {id_str}')
        id_plutus = coerce_ipfs_peerid(id_str)
        LOG.debug(f'id_plutus: {id_plutus}')
        return id_plutus

    # TODO better name
    # TODO is there ever really a NoIpfsNode case here? Maybe don't return option
    def get_own_node(
            self,
            explicit_hints: list[str] = [],
            n_global_hints: int = 4,
            n_local_hints: int = 4,
        ) -> OptionIpfsNode:
        # try:
        # TODO refactor this
        peer_id = self.get_own_peer_id()
        hints = [
            coerce_ipfs_multiaddr(h)
            for h in self.own_addr_hints(
                explicit = explicit_hints,
                n_global = n_global_hints,
                n_local  = n_local_hints,
            )
        ]
        if hints:
            LOG.info(f'first hint type: {type(hints[0])}')   # want: <class 'bytes'>
        LOG.info(f'peer_id type: {type(peer_id)}')       # want: <class 'bytes'>
        # hints = [h for h in hints if len(h) < 64] # TODO fix chunking bug that requires this
        # LOG.info(f'hints < 64b: {hints}')
        return SomeIpfsNode(IpfsNode(peer_id=peer_id, addr_hints=hints))
        # except Exception as e:
        #     LOG.error(e)
        #     return NoIpfsNode()

#     async def add_explicit_peer(self, node: IpfsNode):
#         peer_id = ipfs_peerid_to_string(node.peer_id)
#         LOG.debug(f'peer_id: {peer_id}')
#         hint_addrs = [] # TODO implement these
#         # Build a multiaddr that includes the /p2p/<id> component.
#         # TODO do this for each hint, right?
#         if hint_addrs:
#             addr = hint_addrs[0]
#             maddr = addr if "/p2p/" in addr else f"{addr}/p2p/{peer_id}"
#         else:
#             maddr = f"/p2p/{peer_id}"
#
#         LOG.debug(f'maddr: {maddr}')
#         await self.ipfs._client.swarm.peering.add(maddr)
#         LOG.info(f'added explicit peer {maddr}')

    def set_channel_node(self, channel_id: ChannelId, opt_new: OptionIpfsNode):
        opt_prev = (
            self.channel_nodes[channel_id]
            if channel_id in self.channel_nodes
            else None
        )
        if opt_prev == opt_new:
            return
        ch_str = channel_id_to_string(channel_id)
        LOG.info(f'update {ch_str} channel node: {opt_prev} -> {opt_new}')
        self.channel_nodes[channel_id] = opt_new
        if opt_new == NoIpfsNode():
            return
        peerid_str = ipfs_peerid_to_string(opt_new.value.peer_id)
        if opt_new.value.peer_id == self.get_own_peer_id():
            LOG.info(f'skip peering with own node: {peerid_str}')
        else:
            hints = self.channel_addr_hints(opt_new.value)
            for h in hints:
                # TODO better way to aggregate the async calls?
                LOG.info(f'adding hint {h}')
                self._run_sync(
                    self.ipfs._client.swarm.peering.add(h)
                )

    def expand_addr_hints(self, peer_id: str, addr_hints: list[str]) -> list[str]:
        return expand_addr_hints(peer_id, addr_hints) # TODO same name ok?

    def channel_addr_hints(self, ipfs_node: IpfsNode):
        peerid_str = ipfs_peerid_to_string(ipfs_node.peer_id)
        hints = [ipfs_multiaddr_to_string(h) for h in ipfs_node.addr_hints]
        LOG.info(f'hints before expand: {hints}')
        hints = self.expand_addr_hints(peerid_str, hints)
        LOG.info(f'hints after expand: {hints}')
        return hints

    def all_other_channel_peerid_strs(self) -> list[str]:
        "Used to prioritize own_addr_hints."
        ids = []
        for opt_node in self.channel_nodes.values():
            if opt_node == NoIpfsNode():
                continue
            if opt_node.value.peer_id == self.get_own_peer_id():
                continue
            ids.append(opt_node.value.peer_id)
        return ids

    def all_channel_addr_hints(self):
        nodes = [
            n.value
            for n in self.channel_nodes.values()
            if isinstance(n, SomeIpfsNode)
        ]
        LOG.debug(f'nodes: {nodes}')
        hints = []
        for n in nodes:
            hints += self.channel_addr_hints(n)
        LOG.debug(f'hints: {hints}')
        return sorted(list(set(hints)))

    # TODO return coerced bytes, or the entire IpfsNode type? less footgun
    def own_addr_hints(self, explicit: list[str], n_global: int = 4, n_local: int = 4):
        """List N best guesses at the most useful current addr_hints. Depends
        on channel_node peerids because we especially want to be dialable to
        them. Relays are shortened with `r:` notation, which should be expanded
        with self.expand_addr_hints before use by other nodes."""
        # TODO prepend with any explicit user hints
        # TODO enforce contract limit of 8
        # TODO validate explicit hints
        LOG.debug(f'explicit: {explicit}')
        channel_peerid_strs = self.all_other_channel_peerid_strs()
        LOG.debug(f'channel_peerid_strs: {channel_peerid_strs}')
        global_hints = self._run_sync(
            make_addr_hints(
                self.ipfs._client,
                n_hints        = n_global,
                want_peers     = channel_peerid_strs,
                prefer_lan     = False,
                include_relays = True,
            )
        )
        LOG.debug(f'global_hints: {global_hints}')
        local_hints = self._run_sync(
            make_addr_hints(
                self.ipfs._client,
                n_hints        = n_local,
                want_peers     = channel_peerid_strs,
                prefer_lan     = True,
                include_relays = False,
            )
        )
        LOG.debug(f'local_hints: {local_hints}')
        deduped_hints = []
        for h in explicit + global_hints + local_hints:
            if not h in deduped_hints:
                deduped_hints.append(h)
        LOG.debug(f'deduped_hints: {deduped_hints}')
        return deduped_hints
