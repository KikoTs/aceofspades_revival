# -*- coding: utf-8 -*-
"""HTTPS transport backed by Windows WinHTTP.

The original game ships a Python 2/OpenSSL runtime that predates the TLS
configuration used by modern hosts.  WinHTTP uses the operating system's
current TLS and certificate trust without disabling verification.
"""
from __future__ import print_function

import ctypes
from ctypes import wintypes
import sys

try:
    from urlparse import urlsplit
except ImportError:
    from urllib.parse import urlsplit


class HttpTransportError(Exception):
    pass


def _windows_request(url, method, headers, body, timeout):
    winhttp = ctypes.windll.winhttp

    handle_type = wintypes.HANDLE
    winhttp.WinHttpOpen.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.DWORD,
    ]
    winhttp.WinHttpOpen.restype = handle_type
    winhttp.WinHttpSetTimeouts.argtypes = [
        handle_type,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
    ]
    winhttp.WinHttpConnect.argtypes = [
        handle_type,
        wintypes.LPCWSTR,
        wintypes.WORD,
        wintypes.DWORD,
    ]
    winhttp.WinHttpConnect.restype = handle_type
    winhttp.WinHttpOpenRequest.argtypes = [
        handle_type,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        ctypes.POINTER(wintypes.LPCWSTR),
        wintypes.DWORD,
    ]
    winhttp.WinHttpOpenRequest.restype = handle_type
    winhttp.WinHttpSendRequest.argtypes = [
        handle_type,
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_size_t,
    ]
    winhttp.WinHttpSendRequest.restype = wintypes.BOOL
    winhttp.WinHttpReceiveResponse.argtypes = [handle_type, wintypes.LPVOID]
    winhttp.WinHttpReceiveResponse.restype = wintypes.BOOL
    winhttp.WinHttpQueryHeaders.argtypes = [
        handle_type,
        wintypes.DWORD,
        wintypes.LPCWSTR,
        wintypes.LPVOID,
        ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(wintypes.DWORD),
    ]
    winhttp.WinHttpQueryHeaders.restype = wintypes.BOOL
    winhttp.WinHttpQueryDataAvailable.argtypes = [
        handle_type,
        ctypes.POINTER(wintypes.DWORD),
    ]
    winhttp.WinHttpQueryDataAvailable.restype = wintypes.BOOL
    winhttp.WinHttpReadData.argtypes = [
        handle_type,
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    ]
    winhttp.WinHttpReadData.restype = wintypes.BOOL
    winhttp.WinHttpCloseHandle.argtypes = [handle_type]
    winhttp.WinHttpCloseHandle.restype = wintypes.BOOL

    parsed = urlsplit(url)
    secure = parsed.scheme.lower() == "https"
    if parsed.scheme.lower() not in ("http", "https") or not parsed.hostname:
        raise HttpTransportError("invalid HTTP URL")
    port = parsed.port or (443 if secure else 80)
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query
    hostname = parsed.hostname
    if not isinstance(hostname, type(u"")):
        hostname = hostname.decode("ascii")
    if not isinstance(path, type(u"")):
        path = path.decode("utf-8")
    if not isinstance(method, type(u"")):
        method = method.decode("ascii")

    session = connection = request_handle = None
    try:
        # DEFAULT_PROXY respects the user's Windows proxy configuration.
        session = winhttp.WinHttpOpen(
            u"AoS-Revival-Launcher/1.0",
            0,
            None,
            None,
            0,
        )
        if not session:
            raise ctypes.WinError()
        milliseconds = max(1, int(float(timeout) * 1000))
        if not winhttp.WinHttpSetTimeouts(
            session,
            milliseconds,
            milliseconds,
            milliseconds,
            milliseconds,
        ):
            raise ctypes.WinError()

        connection = winhttp.WinHttpConnect(session, hostname, port, 0)
        if not connection:
            raise ctypes.WinError()
        flags = 0x00800000 if secure else 0  # WINHTTP_FLAG_SECURE
        request_handle = winhttp.WinHttpOpenRequest(
            connection,
            method,
            path,
            None,
            None,
            None,
            flags,
        )
        if not request_handle:
            raise ctypes.WinError()

        header_text = u"\r\n".join(
            u"%s: %s" % (key, value) for key, value in headers.items()
        )
        body = body or b""
        if not isinstance(body, bytes):
            body = body.encode("utf-8")
        body_buffer = ctypes.create_string_buffer(body, len(body)) if body else None
        body_pointer = ctypes.cast(body_buffer, wintypes.LPVOID) if body_buffer else None
        if not winhttp.WinHttpSendRequest(
            request_handle,
            header_text if header_text else None,
            len(header_text) if header_text else 0,
            body_pointer,
            len(body),
            len(body),
            0,
        ):
            raise ctypes.WinError()
        if not winhttp.WinHttpReceiveResponse(request_handle, None):
            raise ctypes.WinError()

        status = wintypes.DWORD()
        status_size = wintypes.DWORD(ctypes.sizeof(status))
        query = 19 | 0x20000000  # STATUS_CODE | QUERY_FLAG_NUMBER
        if not winhttp.WinHttpQueryHeaders(
            request_handle,
            query,
            None,
            ctypes.byref(status),
            ctypes.byref(status_size),
            None,
        ):
            raise ctypes.WinError()

        chunks = []
        while True:
            available = wintypes.DWORD()
            if not winhttp.WinHttpQueryDataAvailable(
                request_handle, ctypes.byref(available)
            ):
                raise ctypes.WinError()
            if available.value == 0:
                break
            buffer_value = ctypes.create_string_buffer(available.value)
            read = wintypes.DWORD()
            if not winhttp.WinHttpReadData(
                request_handle,
                buffer_value,
                available.value,
                ctypes.byref(read),
            ):
                raise ctypes.WinError()
            chunks.append(buffer_value.raw[:read.value])
        return int(status.value), b"".join(chunks)
    except OSError as error:
        raise HttpTransportError(str(error))
    finally:
        for handle in (request_handle, connection, session):
            if handle:
                winhttp.WinHttpCloseHandle(handle)


def request(url, method="GET", headers=None, body=None, timeout=10):
    headers = headers or {}
    if sys.platform == "win32" and hasattr(ctypes, "windll"):
        return _windows_request(url, method, headers, body, timeout)

    # Development-only fallback for non-Windows source checks.
    try:
        import urllib.request as urllib_request
        import urllib.error as urllib_error
    except ImportError:
        import urllib2 as urllib_request
        urllib_error = urllib_request
    request_value = urllib_request.Request(url, data=body, headers=headers)
    request_value.get_method = lambda: method
    try:
        response = urllib_request.urlopen(request_value, timeout=timeout)
        return getattr(response, "code", 200), response.read()
    except urllib_error.HTTPError as error:
        return error.code, error.read()
    except Exception as error:
        raise HttpTransportError(str(error))
