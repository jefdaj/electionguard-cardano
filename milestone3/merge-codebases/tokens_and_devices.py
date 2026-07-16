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
from pycardano import PaymentSigningKey, PaymentVerificationKey


class TokenKind(IntEnum):
    OK_TO_VOTE = 0
    IN_PROGRESS = 1
    FINAL = 2  # optional: issued at challenge station as the end receipt


# ---- canonical signing payload -------------------------------------------------
def _signing_bytes(jti: bytes, kind: int, exp: int,
                   issuer: bytes, cid: bytes) -> bytes:
    # deterministic CBOR array; excludes sig. Order matters.
    return cbor2.dumps([jti, int(kind), int(exp), issuer, cid])


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
    jti: bytes                 # 16 random bytes, the nullifier id
    kind: TokenKind
    exp: int                   # unix seconds
    issuer: bytes              # issuer Ed25519 pubkey (32 bytes)
    cid: bytes = b""           # IPFS CID (raw bytes) when relevant, else empty
    sig: bytes = b""           # 64-byte Ed25519 signature

    # pretty printing

    # def __repr__(self) -> str:
        

    # ---- signing / verification ----
    def _payload(self) -> bytes:
        return _signing_bytes(self.jti, self.kind, self.exp, self.issuer, self.cid)

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
            self.jti, int(self.kind), self.exp, self.issuer, self.cid, self.sig
        ])
        return base64.urlsafe_b64encode(blob).decode()

    @classmethod
    def from_qr_str(cls, s: str) -> "AuthToken":
        jti, kind, exp, issuer, cid, sig = cbor2.loads(
            base64.urlsafe_b64decode(s.encode()))
        return cls(jti, TokenKind(kind), exp, issuer, cid, sig)


# ---- single-use nullifier store (swap for a DB / chain later) -------------------
class NullifierStore:
    """Atomic insert-if-absent. In-memory for now; give it the same interface
    when you move to Redis SETNX or an on-chain mapping."""
    def __init__(self) -> None:
        self._spent: set[bytes] = set()

    def spend(self, jti: bytes) -> bool:
        if jti in self._spent:
            return False
        self._spent.add(jti)
        return True


# ---- stations ------------------------------------------------------------------
DEFAULT_TTL = 15 * 60  # seconds


class Station:
    def __init__(self, sk: PaymentSigningKey, trusted: set[bytes],
                 nullifiers: NullifierStore):
        self.sk = sk
        self.pk = PaymentVerificationKey.from_signing_key(sk).payload  # 32 bytes
        self.trusted = trusted          # set of acceptable issuer pubkeys
        self.nullifiers = nullifiers

    def _issue(self, kind: TokenKind, cid: bytes = b"",
               ttl: int = DEFAULT_TTL) -> AuthToken:
        return AuthToken(
            jti=os.urandom(16), kind=kind, exp=int(time.time()) + ttl,
            issuer=self.pk, cid=cid,
        ).sign(self.sk)

    def _accept(self, tok: AuthToken, expect: TokenKind) -> AuthToken:
        if tok.kind != expect:
            raise ValueError(f"wrong kind: {tok.kind!r}")
        if tok.issuer not in self.trusted:
            raise ValueError("untrusted issuer")
        if not tok.verify():
            raise ValueError("bad signature")
        if tok.expired():
            raise ValueError("expired")
        if not self.nullifiers.spend(tok.jti):  # atomic single-use
            raise ValueError("already spent")
        return tok


# TODO minimal demo: one checkin + one combined challenge/submit?
# TODO or just keep them as 3 separate things for code simplicity

class CheckInStation(Station):
    def check_in(self) -> AuthToken:                     # after eligibility check
        return self._issue(TokenKind.OK_TO_VOTE)

class SubmitStation(Station):
    def submit(self, ok_token: AuthToken, ballot_cid: bytes) -> AuthToken:
        self._accept(ok_token, TokenKind.OK_TO_VOTE)     # consumes OK-to-vote
        # ...ElectionGuard encrypt + publish ciphertext to IPFS happens here...
        return self._issue(TokenKind.IN_PROGRESS, cid=ballot_cid)


class ChallengeStation(Station):
    def challenge(self, ip_token: AuthToken, spoiled: bool,
               final_cid: bytes) -> tuple[AuthToken, Optional[AuthToken]]:
        self._accept(ip_token, TokenKind.IN_PROGRESS)    # consumes in-progress
        # ...record cast/spoil decision in ElectionGuard...
        receipt = self._issue(TokenKind.FINAL, cid=final_cid)
        reissue = self._issue(TokenKind.OK_TO_VOTE) if spoiled else None
        return receipt, reissue

if __name__ == '__main__':
    store = NullifierStore()

    checkin_sk  = PaymentSigningKey.generate()
    submit_sk   = PaymentSigningKey.generate()
    challenge_sk = PaymentSigningKey.generate()

    pk = lambda sk: PaymentVerificationKey.from_signing_key(sk).payload

    # who each station trusts as an issuer of its *input* token:
    submit_trusts    = {pk(checkin_sk), pk(challenge_sk)}   # OK-to-vote sources
    challenge_trusts = {pk(submit_sk)}                       # in-progress source

    checkin   = CheckInStation(checkin_sk, set(), store)     # issues only
    submit    = SubmitStation(submit_sk, submit_trusts, store)
    challenge = ChallengeStation(challenge_sk, challenge_trusts, store)

    ok  = checkin.check_in()
    ok2 = checkin.check_in()
    print(f'\nok: {ok}')
    print(f'\nok2: {ok2}')

    ip  = submit.submit(AuthToken.from_qr_str(ok.to_qr_str()), b"bafk...cid")
    ip2 = submit.submit(AuthToken.from_qr_str(ok2.to_qr_str()), b"bafk...cid")
    print(f'\nip: {ip}')
    print(f'\nip2: {ip2}')

    # correctly fails with "already spent":
    # ip  = submit.submit(AuthToken.from_qr_str(ok.to_qr_str()), b"bafk...cid")

    receipt, ok3 = challenge.challenge(ip, spoiled=True, final_cid=b"bafk...spoil")
    receipt2, ok4 = challenge.challenge(ip2, spoiled=False, final_cid=b"bafk...cast")
    print(f'\nreceipt: {receipt}')
    print(f'\nok3: {ok3}')
    print(f'\nreceipt2: {receipt2}')
    print(f'\nok4: {ok4}')

    ip3 = submit.submit(AuthToken.from_qr_str(ok3.to_qr_str()), b"bafk...cid")
    print(f'\nip3: {ip3}')
    receipt3, ok5 = challenge.challenge(ip3, spoiled=False, final_cid=b"bafk...cast")
    print(f'\nreceipt3: {receipt3}')

    print(f'\ncheckin station state: {checkin.__dict__}')
    print(f'\ncheckin station nullifiers: {checkin.nullifiers.__dict__}')

    print(f'\nsubmit station state: {submit.__dict__}')
    print(f'\nsubmit station nullifiers: {submit.nullifiers.__dict__}')

    print(f'\nchallenge station state: {challenge.__dict__}')
    print(f'\nchallenge station nullifiers: {challenge.nullifiers.__dict__}')
