import aiofiles
from aioipfs import AsyncIPFS
import asyncio
from aiohttp import ClientConnectorError, ClientConnectorDNSError
import os
import tempfile

from .plutus  import *
from .records import *

import logging

LOG = logging.getLogger(__name__)


# TODO hook subscriber callback(s) to ipfs fetch
# TODO extend fetch callbacks to save files -> private dir
# TODO wrapper script: call verifier docker container on private dir after


# TODO set dynamically
# IPFS_MADDR = os.environ.get('IPFS_MADDR', '/dns4/publish-and-verify-ipfs-1/tcp/5001')
IPFS_MADDR = os.environ.get('IPFS_MADDR', '/dns4/127.0.0.1/tcp/5001')
LOG.debug(f'IPFS_MADDR: {IPFS_MADDR}')


class RetryingIPFS:
    def __init__(self, retries=10, delay=1.0, backoff=1.5):
        self._client  = AsyncIPFS(maddr=IPFS_MADDR)
        self._retries = retries
        self._delay   = delay
        self._backoff = backoff

	# support use as an async context manager by delegating to _client
    async def __aenter__(self):
        return self
    async def __aexit__(self, *exc):
        await self._client.close()
    async def close(self):
        await self._client.close()

    async def _retry(self, coro_factory):
        delay = self._delay
        for attempt in range(self._retries):
            try:
                await ipfs_wait_until_ready(self) # TODO make it a method?
                return await coro_factory()
            except (ClientConnectorError, ClientConnectorDNSError) as e:
                if attempt == self._retries - 1:
                    raise
                await asyncio.sleep(delay)
                delay *= self._backoff

    # Wrap only what you need, e.g. add, cat, pin, etc.
    async def add(self, *args, **kwargs):
        kwargs.setdefault('cid_version', 1)
        return await self._retry(lambda: self._client.add(*args, **kwargs))

    async def add_json(self, *args, **kwargs):
        kwargs.setdefault('cid_version', 1)
        return await self._retry(lambda: self._client.add_json(*args, **kwargs))

    async def cat(self, *args, **kwargs):
        return await self._retry(lambda: self._client.cat(*args, **kwargs))

    @property
    def pin(self):
        client_pin = self._client.pin

        class _PinProxy:
            def __init__(_self, outer, inner):
                _self._outer = outer
                _self._inner = inner

            async def add(_self, *args, **kwargs):
                return await _self._outer._retry(
                    lambda: _self._inner.add(*args, **kwargs)
                )

            async def rm(_self, *args, **kwargs):
                return await _self._outer._retry(
                    lambda: _self._inner.rm(*args, **kwargs)
                )

            def __getattr__(_self, name):
                return getattr(_self._inner, name)

        return _PinProxy(self, client_pin)

    # Fallback for anything else – no retries by default:
    def __getattr__(self, name):
        return getattr(self._client, name)


async def ipfs_wait_until_ready(ipfs: RetryingIPFS, timeout=10):
    end = asyncio.get_event_loop().time() + timeout
    while True:
        try:
            await ipfs._client.version()  # raw client, single call
            return
        except (ClientConnectorError, ClientConnectorDNSError):
            if asyncio.get_event_loop().time() > end:
                raise
            await asyncio.sleep(1)


# TODO make this a method of RetryingIPFS?
# TODO take a PublicRecordMetadata here too and return the finished PublicRecord?
async def ipfs_publish_obj(ipfs: RetryingIPFS, obj: dict) -> bytes:
    # Publishes a dict and returns the ipfs_cid bytes, ready for use in PublicRecord.
    added_file = await ipfs.add_json(obj)
    cid_str = added_file['Hash']
    LOG.debug(f'cid_str: {cid_str}')
    cid_bytes = coerce_ipfs_cid(cid_str)
    LOG.debug(f'cid_bytes: {cid_bytes}')
    return cid_bytes


async def ipfs_publish_objs(objs: list[dict]) -> list[bytes]:
    # TODO take ipfs or mk_ipfs as an arg to dynmically configure
    async with RetryingIPFS() as ipfs:
        return await asyncio.gather(
            *(ipfs_publish_obj(ipfs, o) for o in objs)
        )


# TODO take ipfs or mk_ipfs as an arg to dynmically configure
def ipfs_publish_objs_sync(objs: list[dict]) -> list[bytes]:
    with asyncio.Runner() as runner:
        return runner.run( ipfs_publish_objs(objs) )


# TODO make this a method of RetryingIPFS?
async def ipfs_fetch_record_to_file(ipfs: RetryingIPFS, record: PublicRecord, pub_dir: Path):

    # Get destination path
    if not isinstance(pub_dir, Path):
        pub_dir = Path(pub_dir)
    LOG.debug(f'pub_dir: {pub_dir}')
    filename = str(record_path(record.metadata, pub_dir=pub_dir))
    LOG.debug(f'filename: {filename}')

    # Get CID
    cid_str = ipfs_cid_to_string(record.ipfs_cid)
    LOG.debug(f'cid_str: {cid_str}')

    # Get the raw bytes for the CID
    data = await ipfs.cat(cid_str)

    # Ensure parent dir exists
    dir_name = os.path.dirname(filename) # or "."
    os.makedirs(dir_name, exist_ok=True)

    # Create a temp file in the same directory
    fd, tmp_path = tempfile.mkstemp(
        dir=dir_name,
        prefix=".tmp_",
        suffix=".part"
    )
    os.close(fd)  # we'll reopen it with aiofiles

    try:
        # Write to temp file
        async with aiofiles.open(tmp_path, "wb") as f:
            await f.write(data)
            await f.flush()

        # Atomically replace the target file
        os.replace(tmp_path, filename)

        return Path(filename)

    finally:
        # Clean up temp file if anything went wrong before replace
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


async def ipfs_fetch_records_to_file(
        records: list[PublicRecord],
        pub_dir: Path,
    ) -> list[Path]:
    # TODO take ipfs or mk_ipfs as an arg to dynmically configure
    async with RetryingIPFS() as ipfs:
        return await asyncio.gather(
            *(ipfs_fetch_record_to_file(ipfs, r, pub_dir) for r in records)
        )


# TODO take ipfs or mk_ipfs as an arg to dynmically configure
# TODO rewrite with ipfs_run_all_sync
def ipfs_fetch_records_to_file_sync(
        records: list[PublicRecord],
        pub_dir: Path,
    ) -> list[Path]:
    with asyncio.Runner() as runner:
        return runner.run( ipfs_fetch_records_to_file(records, pub_dir=pub_dir) )
