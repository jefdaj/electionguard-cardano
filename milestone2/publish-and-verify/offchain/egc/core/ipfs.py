import aiofiles
# import aioipfs
from aioipfs import AsyncIPFS
import asyncio
import logging
from aiohttp import ClientConnectorError, ClientConnectorDNSError
import os


LOG = logging.getLogger(__name__)


# TODO hook publisher to ipfs upload
# TODO hook subscriber callback(s) to ipfs fetch
# TODO extend fetch callbacks to save files -> private dir
# TODO wrapper script: call verifier docker container on private dir after


# TODO set dynamically
IPFS_MADDR = os.environ.get('IPFS_MADDR', '/dns4/publish-and-verify-ipfs-1/tcp/5001')
LOG.debug(f'IPFS_MADDR: {IPFS_MADDR}')


async def wait_for_ipfs(ipfs, timeout=10):
    end = asyncio.get_event_loop().time() + timeout
    while True:
        try:
            await ipfs._client.version()  # raw client, single call
            return
        except (ClientConnectorError, ClientConnectorDNSError):
            if asyncio.get_event_loop().time() > end:
                raise
            await asyncio.sleep(1)


class RetryingIPFS:
    def __init__(self, retries=10, delay=1.0, backoff=1.5):
        self._client  = AsyncIPFS(maddr=IPFS_MADDR)
        self._retries = retries
        self._delay   = delay
        self._backoff = backoff

    async def _retry(self, coro_factory):
        delay = self._delay
        for attempt in range(self._retries):
            try:
                await wait_for_ipfs(self) # TODO make it a method?
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


# TODO separate the code for actually saving the file from the ipfs code
# TODO would it be better to save to a temporary location and let ipfs put the file in place?
# async def to_public_record(
#         ipfs: RetryingIPFS,
#         channel: str,
#         record_type: str,
#         obj,
#         **fmtargs
#     ):
#     # TODO if adding the file fails, what then? remove locally? retry?
#     fpath = to_record(PUBLIC_RECORDS, record_type, obj, **fmtargs)
#     cid = await publish_on_ipfs(ipfs, obj)
#     fmtargs['cid'] = cid
#     mockchain_post_public_record(channel, record_type, **fmtargs)
#     # TODO return something? cid, bool, res


# def from_public_record(record_type: str, **fmtargs):
#     return from_record(PUBLIC_RECORDS, record_type, **fmtargs)


# def format_to_regex(
#     fmt: str,
#     field_patterns: dict[str, str] | None = None,
#     suffix: str = r'\.json$',
# ) -> Pattern:
#     """
#     Turn a format string like
#       '.../{guardian_id}_backup_{backup_order}'
#     into a regex with named groups.
# 
#     `field_patterns` can override the pattern for specific fields.
#     """
#     formatter = string.Formatter()
#     field_patterns = field_patterns or {}
# 
#     regex_parts = []
# 
#     for literal_text, field_name, format_spec, conversion in formatter.parse(fmt):
#         # Escape literal parts
#         if literal_text:
#             regex_parts.append(re.escape(literal_text))
# 
#         if field_name is None:
#             continue  # no more fields
# 
#         # Pattern for this field: custom or default
#         pat = field_patterns.get(field_name, r'[^/]+')
#         regex_parts.append(f"(?P<{field_name}>{pat})")
# 
#     # Add optional suffix, e.g. file extension
#     if suffix:
#         regex_parts.append(suffix)
# 
#     return re.compile("".join(regex_parts))


# async def fetch_cid_to_file(ipfs: RetryingIPFS, cid: str, filename: str):
#     # Get the raw bytes for the CID
#     data = await ipfs.cat(cid)
# 
#     # Ensure parent dir exists
#     dir_name = os.path.dirname(filename) or "."
#     os.makedirs(dir_name, exist_ok=True)
# 
#     # Create a temp file in the same directory
#     fd, tmp_path = tempfile.mkstemp(
#         dir=dir_name,
#         prefix=".tmp_",
#         suffix=".part"
#     )
#     os.close(fd)  # we'll reopen it with aiofiles
# 
#     try:
#         # Write to temp file
#         async with aiofiles.open(tmp_path, "wb") as f:
#             await f.write(data)
#             await f.flush()
# 
#         # Atomically replace the target file
#         os.replace(tmp_path, filename)
#     finally:
#         # Clean up temp file if anything went wrong before replace
#         if os.path.exists(tmp_path):
#             try:
#                 os.remove(tmp_path)
#             except OSError:
#                 pass


# async def publish_on_ipfs(ipfs: RetryingIPFS, obj: dict) -> str:
#     added_file = await ipfs.add_json(obj)
#     cid = added_file['Hash'] # TODO is this a dict in this aioipfs version?
#     return cid


# TODO should this go through MockchainSubscriber instead? or is separate more robust?
# def next_json_path(channel: str) -> str:
#     channel_dir = join(MOCKCHAIN_JSON_DIR, channel)
#     index = 1
#     while True:
#         json_path = join(channel_dir, f'{index:03d}.json')
#         if not exists(json_path):
#             return json_path
#         index += 1


# TODO how to post a list of records rather than just one? need some kind of queue?
# TODO cid type?
# def mockchain_post_public_record(channel: str, record_type: str, **post_json):
#     post_json['record_type'] = record_type
#     mockchain_post_json(channel, 'post_public_record', **post_json)


