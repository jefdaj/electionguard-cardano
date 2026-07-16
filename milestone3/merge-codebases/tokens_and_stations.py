#!/usr/bin/env python3

from __future__ import annotations
import base64, os, time
from dataclasses import dataclass, field, fields, asdict
from enum import IntEnum
from typing import Optional

import json

import cbor2
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from pycardano import PaymentSigningKey, PaymentVerificationKey, VerificationKeyHash

from egc.core import qrcodes


class TokenKind(IntEnum):
    OK_TO_VOTE = 0
    VOTE_IN_PROGRESS = 1
    I_VOTED = 2  # optional: issued at challenge station as the end receipt


# ---- canonical signing payload -------------------------------------------------
def _signing_bytes(kind: int, jti: bytes, exp: int,
                   issuer: bytes, cid: bytes) -> bytes:
    # deterministic CBOR array; excludes sig. Order matters.
    return cbor2.dumps([int(kind), jti, int(exp), issuer, cid])


class HexReprMixin:
    def __repr__(self):
        parts = []
        for f in fields(self):
            v = getattr(self, f.name)
            v = "'" + v.hex() + "'" if isinstance(v, (bytes, bytearray)) else repr(v)
            parts.append(f"{f.name}={v}")
        return f"{type(self).__name__}({', '.join(parts)})"


@dataclass(repr=False)
class AuthToken(HexReprMixin):
    kind: TokenKind
    jti: bytes                 # 16 random bytes, the nullifier id
    exp: int                   # unix seconds
    issuer: bytes              # issuer Ed25519 pubkey (32 bytes)
    cid: bytes = b""           # IPFS CID (raw bytes) when relevant, else empty
    sig: bytes = b""           # 64-byte Ed25519 signature

    # ---- signing / verification ----
    def _payload(self) -> bytes:
        return _signing_bytes(self.kind, self.jti, self.exp, self.issuer, self.cid)

    def sign(self, sk: PaymentSigningKey) -> "AuthToken":
        self.sig = sk.sign(self._payload())
        return self

    def verify(self) -> bool:
        try:
            VerifyKey(self.issuer).verify(self._payload(), self.sig)
        except BadSignatureError:
            return False
        return True

    def expired(self, now: Optional[int] = None) -> bool:
        return (now or int(time.time())) > self.exp

    # ---- QR (matches your existing pattern) ----
    def to_qr_str(self) -> str:
        blob = cbor2.dumps([
            int(self.kind), self.jti, self.exp, self.issuer, self.cid, self.sig
        ])
        blob = base64.urlsafe_b64encode(blob).decode()
        qr_str = ':'.join([
            'egc',
            token_prefix(self), # this is extra for human readability
            blob
        ])
        return qr_str

    @classmethod
    def from_qr_str(cls, s: str) -> "AuthToken":
        txt = ''.join(l.strip() for l in s.splitlines())
        words = txt.split(':')
        prefix = words[:2]
        assert prefix[0] == 'egc'
        assert prefix[1] in ['oktovote', 'voteinprogress', 'ivoted']
        blob = words[2]
        kind, jti, exp, issuer, cid, sig = cbor2.loads(
            base64.urlsafe_b64decode(blob.encode()))
        return cls(TokenKind(kind), jti, exp, issuer, cid, sig)


def token_prefix(tok: AuthToken) -> str:
    return str(tok.kind.name).lower().replace('_', '')


# ---- single-use nullifier store (swap for a DB / chain later) -------------------

class HexByteSet(set):
    "Just makes a set[bytes] more human readable."
    def __repr__(self):
        return "{" + ", ".join(
            v.hex() if isinstance(v, (bytes, bytearray)) else repr(v)
            for v in self
        ) + "}"
    def __or__(self, o):  return HexByteSet(super().__or__(o))
    def __and__(self, o): return HexByteSet(super().__and__(o))
    def __sub__(self, o): return HexByteSet(super().__sub__(o))
    def __xor__(self, o): return HexByteSet(super().__xor__(o))
    def copy(self):       return HexByteSet(self)


class NullifierStore:
    """Atomic insert-if-absent. In-memory for now; give it the same interface
    when you move to Redis SETNX or an on-chain mapping."""
    def __init__(self) -> None:
        self._spent = HexByteSet()

    def spend(self, jti: bytes) -> bool:
        if jti in self._spent:
            return False
        self._spent.add(jti)
        return True

# ---- trust registry -----

class TrustRegistry:
    """Wraps the on-chain set of authorized issuer hashes."""
    def __init__(self, hashes: set[VerificationKeyHash]):
        self._hashes = hashes  # normalized from chain

    def is_trusted(self, issuer: bytes) -> bool:
        vk = PaymentVerificationKey.from_primitive(issuer)
        return vk.hash() in self._hashes

    def refresh(self, hashes: set[VerificationKeyHash]) -> None:
        self._hashes = hashes


def verify_token(tok: AuthToken, registry: TrustRegistry) -> None:
    # 1. authorization: issuer hash on chain
    if not registry.is_trusted(tok.issuer):
        raise PermissionError("issuer not in trust set")
    # 2. authentication: signature valid for that pubkey
    try:
        VerifyKey(tok.issuer).verify(tok._payload(), tok.sig)
    except BadSignatureError:
        raise PermissionError("bad signature")
    # 3. freshness
    if tok.exp < int(time.time()):
        raise PermissionError("expired")


# ---- stations ------------------------------------------------------------------
DEFAULT_TTL = 15 * 60  # seconds


class Station:
    def __init__(self, sk: PaymentSigningKey, registry: TrustRegistry,
                 nullifiers: NullifierStore):
        self.sk = sk
        self.pk = PaymentVerificationKey.from_signing_key(sk).payload  # 32 bytes
        self.registry = registry
        self.nullifiers = nullifiers

    def _issue(self, kind: TokenKind, cid: bytes = b"",
               ttl: int = DEFAULT_TTL) -> AuthToken:
        return AuthToken(
            kind=kind, jti=os.urandom(16), exp=int(time.time()) + ttl,
            issuer=self.pk, cid=cid,
        ).sign(self.sk)

    def _accept(self, tok: AuthToken, expected: TokenKind) -> AuthToken:
        verify_token(tok, self.registry)
        if tok.kind != expected:
            raise PermissionError(f"expected {expected}, got {tok.kind}")
        if not self.nullifiers.spend(tok.jti):   # atomic single-use
            raise PermissionError("token already spent")
        if not tok.verify():
            raise ValueError("bad signature")
        if tok.expired():
            raise ValueError("expired")
        return tok


class CheckInStation(Station):
    # initial ok-to-vote
    def check_in(self) -> AuthToken: # after eligibility check
        return self._issue(TokenKind.OK_TO_VOTE)

class SubmitStation(Station):
    # ok-to-vote -> vote-in-progress
    def submit(self, ok_token: AuthToken, ballot_cid: bytes) -> AuthToken:
        self._accept(ok_token, TokenKind.OK_TO_VOTE) # consumes OK-to-vote
        # ...ElectionGuard encrypt + publish ciphertext to IPFS happens here...
        return self._issue(TokenKind.VOTE_IN_PROGRESS, cid=ballot_cid)


class ChallengeStation(Station):
    # vote-in-progress -> (i-voted, optional ok-to-vote)
    def challenge(self, ip_token: AuthToken, spoiled: bool,
               final_cid: bytes) -> tuple[AuthToken, Optional[AuthToken]]:
        self._accept(ip_token, TokenKind.VOTE_IN_PROGRESS)    # consumes in-progress
        # ...record cast/spoil decision in ElectionGuard...
        receipt = self._issue(TokenKind.I_VOTED, cid=final_cid)
        reissue = self._issue(TokenKind.OK_TO_VOTE) if spoiled else None
        return receipt, reissue

if __name__ == '__main__':
    store = NullifierStore()

    checkin_sk   = PaymentSigningKey.generate()
    submit_sk    = PaymentSigningKey.generate()
    challenge_sk = PaymentSigningKey.generate()
    
    print(f'checkin_sk: {checkin_sk}\n')
    print(f'submit_sk: {submit_sk}\n')
    print(f'challenge_sk: {challenge_sk}\n')

    pk  = lambda sk: PaymentVerificationKey.from_signing_key(sk).payload
    vkh = lambda sk: PaymentVerificationKey.from_primitive(pk(sk)).hash()

    # who each station trusts as an issuer of its *input* token:
    # TODO these should be assembled from onchain channel publishers
    submit_vkh_set    = {vkh(checkin_sk), vkh(challenge_sk)} # ok-to-vote sources
    challenge_vkh_set = {vkh(submit_sk)}                     # vote-in-progress source

    checkin_registry   = TrustRegistry(set()) # checkin only creates new tokens
    submit_registry    = TrustRegistry(submit_vkh_set)
    challenge_registry = TrustRegistry(challenge_vkh_set)
    
    print(f'checkin_registry: {checkin_registry.__dict__}\n')
    print(f'submit_registry: {submit_registry.__dict__}\n')
    print(f'challenge_registry: {challenge_registry.__dict__}\n')
    
    # correctly fails with "untrusted issuer" when submitting ok1:
    # submit_trusts = {pk(challenge_sk)}

    # correctly fails with "untrusted issuer" when submitting ok3:
    # submit_trusts = {pk(checkin_sk)}

    # correctly fails with "untrusted issuer" when submitting ip1
    # challenge_trusts = {} # vote-in-progress source

    checkin_station   = CheckInStation(checkin_sk, set(), store)     # issues only
    submit_station    = SubmitStation(submit_sk, submit_registry, store)
    challenge_station = ChallengeStation(challenge_sk, challenge_registry, store)

    print('check_in 1')
    ok1 = checkin_station.check_in()
    print(f'\nok1: {ok1}')
    print(f'\nok1 verify: {ok1.verify()}\n')
    qrcodes.print_qrcode(ok1)

    print('check_in 2')
    ok2 = checkin_station.check_in()
    print(f'\nok2: {ok2}')
    print(f'\nok2 verify: {ok2.verify()}\n')
    qrcodes.print_qrcode(ok2)
    
    print('submit 1')
    ip1 = submit_station.submit(AuthToken.from_qr_str(ok1.to_qr_str()), b"bafk...cid")
    print(f'\nip1: {ip1}')
    print(f'\nip1 verify: {ip1.verify()}\n')
    qrcodes.print_qrcode(ip1)

    print('submit 2')
    ip2 = submit_station.submit(AuthToken.from_qr_str(ok2.to_qr_str()), b"bafk...cid")
    print(f'\nip2: {ip2}')
    print(f'\nip2 verify: {ip2.verify()}\n')
    qrcodes.print_qrcode(ip2)

    # correctly fails with "already spent":
    # ip1_again = submit.submit(AuthToken.from_qr_str(ok1.to_qr_str()), b"bafk...cid")

    print('spoil 1, creating ok3')
    r1, ok3 = challenge_station.challenge(ip1, spoiled=True, final_cid=b"bafk...spoil")
    print(f'\nr1: {r1}')
    print(f'\nr1 verify: {r1.verify()}\n')
    qrcodes.print_qrcode(r1)
    print(f'\nok3: {ok3}')
    print(f'\nok3 verify: {ok3.verify()}\n')
    qrcodes.print_qrcode(ok3)

    print('cast 2')
    r2, ok4 = challenge_station.challenge(ip2, spoiled=False, final_cid=b"bafk...cast")
    print(f'\nr2: {r2}')
    print(f'\nr2 verify: {r2.verify()}\n')
    qrcodes.print_qrcode(r2)
    assert ok4 is None
    print(f'\nok4: {ok4}\n')

    print('submit 3')
    ip3 = submit_station.submit(AuthToken.from_qr_str(ok3.to_qr_str()), b"bafk...cid")
    print(f'\nip3: {ip3}')
    print(f'\nip3 verify: {ip3.verify()}\n')
    qrcodes.print_qrcode(ip3)

    print('cast 3')
    r3, ok5 = challenge_station.challenge(ip3, spoiled=False, final_cid=b"bafk...cast")
    print(f'\nr3: {r3}')
    print(f'\nr3 verify: {r3.verify()}\n')
    qrcodes.print_qrcode(r3)
    assert ok5 is None
    print(f'\nok5: {ok5}\n')

    print(f'\nfinal checkin station state: {checkin_station.__dict__}')
    print(f'\nfinal submit station state: {submit_station.__dict__}')
    print(f'\nfinal challenge station state: {challenge_station.__dict__}')

    print(f'\nfinal nullifier store: {store._spent}')
