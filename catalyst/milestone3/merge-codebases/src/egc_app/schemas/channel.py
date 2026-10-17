from pydantic import BaseModel, field_validator
from typing import Annotated, Optional, Self
from egc import is_valid_role, is_valid_channel_str
from pycardano import VerificationKeyHash

import logging
LOG = logging.getLogger(__name__)

# TODO move to a util module:
from .election import VerificationKeyHashType

class ChannelAwait(BaseModel):
    role: str

    @field_validator('role')
    def check_role(cls, v: str) -> str:
        assert is_valid_role(v)
        return v

class ChannelAwaitOut(BaseModel):
    channel_str: str

    @field_validator('channel_str')
    def check_role(cls, v: str) -> str:
        assert is_valid_channel_str(v)
        return v

class ChannelRequest(BaseModel):
    requested_role: str

class ChannelRequestOut(BaseModel):
    "The finished request returned from the server, ready to share."

    requested_role: str
    election_oneshot_hex: str
    election_network_magic: int
    publisher_vkh: VerificationKeyHashType
    # TODO schema_version?

    @classmethod
    def from_qr_str(cls, txt: str) -> Self:
        "egc:request:<role>:<oneshot_hex>:<network_magic>:<publisher_vkh>, maybe with wrapping"
        txt = ''.join(l.strip() for l in txt.splitlines())
        LOG.debug(f'from_qr_str txt: {txt}')
        words = txt.split(':')
        prefix = words[:2]
        args   = words[2:]
        assert prefix == ['egc', 'request']
        assert len(args) == 4
        role, oneshot_hex, network_magic, publisher_vkh = args
        network_magic  = int(network_magic)
        publisher_vkh = VerificationKeyHash.from_primitive(publisher_vkh)
        return cls(
            requested_role         = role,
            election_oneshot_hex   = oneshot_hex,
            election_network_magic = network_magic,
            publisher_vkh          = publisher_vkh
        )

    def to_qr_str(self) -> str:
        "egc:request:<role>:<oneshot_hex>:<network_magic>:<publisher_vkh>"
        qr_str = ':'.join([
            'egc', 'request',
            self.requested_role,
            self.election_oneshot_hex,
            str(self.election_network_magic),
            str(self.publisher_vkh), # TODO is this right?
        ])
        return qr_str

class ChannelCreate(BaseModel):
    requests: list[ChannelRequestOut]
    ada_per_channel: int
    done_onboarding: bool # if True, advance phase
