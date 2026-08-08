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

import logging

LOG = logging.getLogger(__name__)


IPFS_API_ADDR = os.environ.get('IPFS_API_ADDR', '/dns4/127.0.0.1/tcp/5001')
LOG.info(f'IPFS_API_ADDR: {IPFS_API_ADDR}')


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
        LOG.info(f'remove {record}')
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
        retry_concurrency=2, # bounded => can't hog the node
        sweep_interval=5,    # how often the sweeper wakes
        base_delay=3,        # first retry backoff
        max_delay=600,       # retry-forever settles to every 10 min
        backoff=2.0
    ):

        self.records_to_post_dir = records_to_post_dir
        self.records_fetched_dir = records_fetched_dir

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
            LOG.info(f'newly published record: {record}')
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
                # TODO does the callback work?
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
            connected = True
        except Exception as e:
            LOG.error(e)
            peers = []
        try:
            bw = await self.ipfs._client.stats.bw()
            rate = int(bw.get("RateIn", 0) + bw.get("RateOut", 0))
            connected = True
        except Exception as e:
            LOG.error(e)
            rate = 0
        return {
            'connected': connected,
            'n_peers': len(peers),
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
        min_peers=3,
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
