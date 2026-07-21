# -*- coding: utf-8 -*-
"""Small RFC 8032 Ed25519 signer for the Python 2.7 launcher.

The legacy client cannot depend on a modern native crypto wheel.  This module
implements only the operations the launcher needs: deriving a public key and
signing the master service's short guest challenge.  Verification remains on
the Node.js service using its platform Ed25519 implementation.
"""
from __future__ import division

import base64
import hashlib
import os


P = 2 ** 255 - 19
Q = 2 ** 252 + 27742317777372353535851937790883648493


def _inverse(value):
    return pow(value, P - 2, P)


D = (-121665 * _inverse(121666)) % P
I = pow(2, (P - 1) // 4, P)


def _xrecover(y):
    xx = (y * y - 1) * _inverse(D * y * y + 1)
    x = pow(xx, (P + 3) // 8, P)
    if (x * x - xx) % P != 0:
        x = (x * I) % P
    if x % 2:
        x = P - x
    return x


BASE_Y = (4 * _inverse(5)) % P
BASE_POINT = (_xrecover(BASE_Y), BASE_Y)
IDENTITY = (0, 1)


def _as_bytes(value):
    if isinstance(value, bytearray):
        return bytes(value)
    if not isinstance(value, bytes):
        return value.encode("utf-8")
    return value


def _byte_values(value):
    value = _as_bytes(value)
    for item in value:
        yield item if isinstance(item, int) else ord(item)


def _decode_little(value):
    result = 0
    for index, item in enumerate(_byte_values(value)):
        result += item << (8 * index)
    return result


def _encode_little(value, length):
    return bytes(bytearray((value >> (8 * index)) & 0xff for index in range(length)))


def _add(left, right):
    x1, y1 = left
    x2, y2 = right
    denominator = D * x1 * x2 * y1 * y2
    x3 = (x1 * y2 + x2 * y1) * _inverse(1 + denominator)
    y3 = (y1 * y2 + x1 * x2) * _inverse(1 - denominator)
    return x3 % P, y3 % P


def _multiply(point, scalar):
    result = IDENTITY
    addend = point
    while scalar:
        if scalar & 1:
            result = _add(result, addend)
        addend = _add(addend, addend)
        scalar >>= 1
    return result


def _encode_point(point):
    x, y = point
    encoded = bytearray(_encode_little(y, 32))
    encoded[31] = encoded[31] | ((x & 1) << 7)
    return bytes(encoded)


def _secret_scalar(digest):
    raw = list(_byte_values(digest[:32]))
    raw[0] &= 248
    raw[31] &= 63
    raw[31] |= 64
    return _decode_little(bytes(bytearray(raw)))


def public_key(seed):
    seed = _as_bytes(seed)
    if len(seed) != 32:
        raise ValueError("Ed25519 seed must be exactly 32 bytes")
    digest = hashlib.sha512(seed).digest()
    return _encode_point(_multiply(BASE_POINT, _secret_scalar(digest)))


def sign(seed, message):
    seed = _as_bytes(seed)
    message = _as_bytes(message)
    if len(seed) != 32:
        raise ValueError("Ed25519 seed must be exactly 32 bytes")
    digest = hashlib.sha512(seed).digest()
    scalar = _secret_scalar(digest)
    public = _encode_point(_multiply(BASE_POINT, scalar))
    nonce = _decode_little(hashlib.sha512(digest[32:] + message).digest()) % Q
    encoded_nonce = _encode_point(_multiply(BASE_POINT, nonce))
    challenge = _decode_little(
        hashlib.sha512(encoded_nonce + public + message).digest()
    ) % Q
    return encoded_nonce + _encode_little((nonce + challenge * scalar) % Q, 32)


def new_seed():
    return os.urandom(32)


def b64url_encode(value):
    encoded = base64.urlsafe_b64encode(_as_bytes(value))
    if not isinstance(encoded, str):
        encoded = encoded.decode("ascii")
    return encoded.rstrip("=")


def b64url_decode(value):
    if not isinstance(value, bytes):
        value = value.encode("ascii")
    value += b"=" * ((4 - len(value) % 4) % 4)
    return base64.urlsafe_b64decode(value)
