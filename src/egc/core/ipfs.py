import aiofiles
import asyncio
import os
import random
import threading
import time
import hashlib
import shutil

from aiohttp import ClientConnectorError, ClientConnectorDNSError
import aioipfs

from .plutus  import *
from .records import *

from .ipfs_hints import make_addr_hints, expand_addr_hints

from .utils import make_log_call
import logging

LOG = logging.getLogger(__name__)
LOG_CALL = make_log_call(log_fn=LOG.debug)


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
        LOG_CALL()
        self._client  = aioipfs.AsyncIPFS(maddr=maddr)
        self._retries = retries
        self._delay   = delay
        self._backoff = backoff

    async def close(self):
        LOG_CALL()
        await self._client.close()

    async def _retry(self, coro_factory):
        LOG_CALL()
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
        LOG_CALL()
        k.setdefault('cid_version', 1)
        return await self._retry(lambda: self._client.add(*a, **k))

    async def add_json(self, *a, **k):
        LOG_CALL()
        k.setdefault('cid_version', 1)
        return await self._retry(lambda: self._client.add_json(*a, **k))

    async def cat(self, *a, **k):
        LOG_CALL()
        return await self._retry(lambda: self._client.cat(*a, **k))

    async def get(self, *a, **k):
        LOG_CALL()
        return await self._retry(lambda: self._client.get(*a, **k))

    async def pin_add(self, *a, **k):
        LOG_CALL()
        return await self._retry(lambda: self._client.pin.add(*a, **k))

    def __getattr__(self, name): # fallback, no retries
        LOG_CALL()
        return getattr(self._client, name)


def _hash(path: Path, chunk=64*1024) -> str:
    # TODO any subtle serialization issues here?
    LOG_CALL()
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


class IPFSService:
    """Handles all IFPS calls for a single EGC node, including:
    - publishing new records posted on chain by the node
    - fetching and pinning records posted on chain by others
    - recovering from a "stuck" IPFS node and other errors
    Owns the event loop, both lanes, and the store.
    """

    # TODO tune these defaults based on test data
    def __init__(self,
        # records_posting_dir: Path,
        # records_verified_dir: Path,
        store: RecordStore,
        maddr=IPFS_API_ADDR,
        fresh_concurrency=2,
        fresh_timeout=10,    # short: withheld CIDs fail fast
        retry_timeout=30,    # patient: give real files a chance
        retry_concurrency=2, # bounded => can't hog the node
        sweep_interval=5,    # how often the sweeper wakes
        base_delay=1,        # first retry backoff
        max_delay=30,       # retry-forever settles to every 10 min
        backoff=1.5
    ):
        LOG_CALL()

        # self.records_posting_dir  = records_posting_dir
        # self.records_verified_dir = records_verified_dir

        # These are set by the node's on_channel_event handler.
        self.channel_nodes: dict[ChannelId, OptionIpfsNode] = {}

        self.maddr = maddr
        self.fresh_concurrency = fresh_concurrency
        self.fresh_timeout = fresh_timeout
        self.retry_timeout = retry_timeout
        self.sweep_interval = sweep_interval
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff = backoff

        self._retry_concurrency = retry_concurrency

        self.ipfs = None
        self.store = store
        self._fresh_q = None
        self._retry_sem = None
        self._inflight = set() # CIDs being fetched right now (dedup)

        # For detecting whether data transfers are stuck.
        # (monotonic_time, blocks_sent, blocks_recv) at last meaningful poll
        self._last_bitswap_snapshot: tuple[float, int, int] | None = None

        # CIDs pending fetch. Some may also be inflight.
        # TODO use cid strs rather than actual cids?
        self._pending: dict[IpfsCid, tuple[int, float]] = {} # TODO is float right?

        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._ready = threading.Event()


    def _run_loop(self):
        "Lifecycle."
        LOG_CALL()
        asyncio.set_event_loop(self._loop)
        self.ipfs = RetryingIPFS(self.maddr)
        # self.store = RecordStore(self.records_verified_dir, eslf.records_rejected_dir)
        self._fresh_q = asyncio.Queue()
        self._retry_sem = asyncio.Semaphore(self._retry_concurrency)

        self._tasks = set()
        coros = [self._fresh_worker() for _ in range(self.fresh_concurrency)]
        coros += [self._sweeper(), self._watchdog()]
        for c in coros:
            t = self._loop.create_task(c)
            self._tasks.add(t)
            t.add_done_callback(self._on_task_done)

        # for _ in range(self.fresh_concurrency):
        #     self._loop.create_task(self._fresh_worker())
        # self._loop.create_task(self._sweeper())
        # self._loop.create_task(self._watchdog())

        self._ready.set()

        # self._loop.run_forever()
        try:
            self._loop.run_forever()
        finally:
            self._loop.run_until_complete(self._loop.shutdown_asyncgens())
            self._loop.close()


    def _on_task_done(self, t):
        self._tasks.discard(t)
        if not t.cancelled() and (exc := t.exception()) is not None:
            LOG.error("Task %s failed", t.get_name(), exc_info=exc)


    async def _shutdown(self):
        for t in self._tasks:
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)  # retrieves everything
        await self.ipfs.close()          # only after the workers are gone
        self._loop.stop()


    def start(self):
        LOG_CALL()
        self._thread.start()
        self._ready.wait()

    def stop(self):
        LOG_CALL()
        # asyncio.run_coroutine_threadsafe(self.ipfs.close(), self._loop).result(10)
        # self._loop.call_soon_threadsafe(self._loop.stop)
        asyncio.run_coroutine_threadsafe(self._shutdown(), self._loop).result(10)
        self._thread.join(10)

    def _run_sync(self, coro, timeout: float | None = None):
        "Call an async method from a sync context (a DIFFERENT thread). All calls should go through one of these?"
        LOG_CALL()
        fut = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return fut.result(timeout) # blocks, re-raises exceptions here

    async def _run_async(self, coro, timeout=None):
        "Call an async method from for example FastAPI. All calls should go through one of these?"
        LOG_CALL()
        fut = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return await asyncio.wait_for(asyncio.wrap_future(fut), timeout)

    def _accept(self, record):
        LOG_CALL()
        cid = record.ipfs_cid
        # self.store.add_record_seen_on_chain(record) # TODO remove? should be redundant
        self._pending[cid] = (0, 0) # TODO is this right?
        self._fresh_q.put_nowait((cid, 0)) # then attempt promptly

    def fetch_record_soon(self, record):
        "Called from the subscriber thread. Returns immediately."
        LOG_CALL()
        self._loop.call_soon_threadsafe(self._accept, record)

    def publish_and_make_record(self, data: dict, metadata: PublicRecordMetadata) -> PublicRecord:
        "Publish data to IPFS and return a new record, ready to post onchain."
        LOG_CALL()
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
        LOG_CALL()
        # TODO how should we handle failures partway through here?
        records = []
        for (data, metadata) in pairs:
            record = self.publish_and_make_record(data, metadata)
            LOG.info(f'published {record}')
            records.append(record)
        return records

    async def _attempt_fetch(self, cid, timeout):
        "The one fetch primitive both lanes share."
        LOG_CALL()
        LOG.debug(f'attempt fetch {cid} n inflight={len(self._inflight)}')
        # key = record_key(record)
        if cid in self._inflight: # never fetch same CID twice at once
            return False
        self._inflight.add(cid)
        cid_str = ipfs_cid_to_string(cid)
        try:
            data = await self._run_async(self.ipfs.cat(cid_str), timeout=timeout)
            async for pin_status in self.ipfs._client.pin.add(cid_str):
                LOG.debug(f'progress pinning {cid_str}: {pin_status}')
            self.store.fetch_successful(cid, data) # success => no longer pending
            del self._pending[cid]
            LOG.info("fetched %s", cid_str)
            return True
        except asyncio.TimeoutError:
            return False # file not propagated to ipfs node yet
        except aioipfs.APIError as e:
            LOG.error(f'fetch error {cid_str}: code={e.code} '
                      f'http={e.http_status} msg={e.message}')
        except Exception as e:
            LOG.error("fetch error %s: %s", cid_str, e)
        # return False # keep it pending, retry later
        finally:
            self._inflight.discard(cid)

    async def _fresh_worker(self):
        "Fresh lane: prompt, short timeout, one shot each."
        LOG_CALL()
        while True:
            cid, _ = await self._fresh_q.get()
            try:
                ok = await self._attempt_fetch(cid, self.fresh_timeout)
                if not ok:
                    self._schedule_retry(cid, attempts=1) # demote to slow lane
            finally:
                self._fresh_q.task_done()

    def mark_attempt(self, cid, attempts, next_attempt):
        LOG_CALL()
        # LOG.debug(f'all records: {self._all_records}')
        # keys = self.keys_for_cid(cid)
        # LOG.debug(f'keys for cid {cid}: {keys}')
        # for key in keys:
        #     LOG.info(f'mark_attempt key:{key} attempts:{attempts} next_attempt:{next_attempt}')
        #     (record, _, _) = self._records_pending_fetch[key] # TODO only track cids, not records?
        #     self._records_pending_fetch[key] = (record, attempts, next_attempt)
        # cid_str = ipfs_cid_to_string(cid)
        self._pending[cid] = (attempts, next_attempt)

    def _schedule_retry(self, cid, attempts):
        "Jitter to prevent all test nodes retrying at once."
        LOG_CALL()
        cap = min(self.base_delay * self.backoff ** (attempts - 1), self.max_delay)
        delay = random.uniform(0, cap) # full jitter
        self.mark_attempt(cid, attempts, time.time() + delay)

    async def _ipfs_is_reachable(self) -> bool:
        """Lightweight check — returns False if the IPFS node is down."""
        LOG_CALL()
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
        LOG_CALL()
        if not await self._ipfs_is_reachable():
            LOG.warning('ipfs node is unreachable; skipping stuck check')
            return False # not "stuck" in the reconnectable sense — nothing to reconnect to
        try:
            stat = await self.ipfs._client.bitswap.stat()
        except Exception as e:
            LOG.warning(f'failed to get bitswap stat; skipping stuck check: {e}')
            return False
        if stat is None:
            LOG.debug('bitswap stat returned None; skipping stuck check')
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
        return (now - snap_time) >= IPFS_STUCK_WINDOW

    async def _force_reconnect(self, maddr: str):
        LOG_CALL()
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
        LOG_CALL()
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

    def due(self, now):
        LOG_CALL()
        # TODO should this live here or in IPFSService?
        cids_due = [
            # (record.ipfs_cid, attempts)
            # for (record, attempts, next_attempt) in self._records_pending_fetch.values()
            # if next_attempt <= now
            (cid, attempts)
            for (cid, (attempts, next_attempt)) in self._pending.items()
            if next_attempt <= now
        ]
        if cids_due:
            LOG.debug(f'cids_due: {len(cids_due)}')
        random.shuffle(cids_due) # TODO is this a good strategy? or should they be sorted?
        return cids_due

    async def _sweeper(self, jitter=True):
        """Retry lane: patient, bounded, forever, on a slow cadence.
        Jitter to prevent all test nodes sweeping at once.
        """
        LOG_CALL()
        while True:
            interval = self.sweep_interval
            if jitter:
                interval *= random.uniform(0.8, 1.2)
            await asyncio.sleep(interval)
            now = time.time()
            for cid, attempts in self.due(now):
                # key = record_key(record)
                if cid in self._inflight:
                    continue
                await self._retry_sem.acquire()
                task = self._loop.create_task(self._retry_one(cid, attempts))
                task.add_done_callback(
                    lambda t: t.exception() and LOG.error(t.exception())
                )

    async def _retry_one(self, cid, attempts):
        LOG_CALL()
        try:
            ok = await self._attempt_fetch(cid, self.retry_timeout)
            if not ok:
                self._schedule_retry(cid, attempts + 1) # cap keeps it periodic
        finally:
            self._retry_sem.release()

    async def _status(self):
        LOG_CALL()
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
        LOG_CALL()
        return await self._run_async(self._status()) # TODO timeout?

    def status_sync(self):
        LOG_CALL()
        return self._run_sync(self._status())

    def count_pending_cids(self):
        LOG_CALL()
        return len(self._pending)

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
        LOG_CALL()
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
        LOG_CALL()
        return self._run_sync(self.wait_until_stable(*args, **kwargs))

    def get_own_peer_id(self) -> IpfsPeerId:
        LOG_CALL()
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
        LOG_CALL()
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
        LOG_CALL()
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
        LOG_CALL()
        return expand_addr_hints(peer_id, addr_hints) # TODO same name ok?

    def channel_addr_hints(self, ipfs_node: IpfsNode):
        LOG_CALL()
        peerid_str = ipfs_peerid_to_string(ipfs_node.peer_id)
        hints = [ipfs_multiaddr_to_string(h) for h in ipfs_node.addr_hints]
        LOG.info(f'hints before expand: {hints}')
        hints = self.expand_addr_hints(peerid_str, hints)
        LOG.info(f'hints after expand: {hints}')
        return hints

    def all_other_channel_peerid_strs(self) -> list[str]:
        "Used to prioritize own_addr_hints."
        LOG_CALL()
        ids = []
        for opt_node in self.channel_nodes.values():
            if opt_node == NoIpfsNode():
                continue
            if opt_node.value.peer_id == self.get_own_peer_id():
                continue
            ids.append(opt_node.value.peer_id)
        return ids

    def all_channel_addr_hints(self):
        LOG_CALL()
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
        LOG_CALL()
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
