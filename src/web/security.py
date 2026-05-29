"""Authentication and path-safety helpers for the Vivisect web GUI.

The web GUI exposes high-impact forensic capabilities (disk imaging, memory
dumps, arbitrary path access, USB HID injection). This module provides the
primitives used by ``app.py`` to keep those capabilities from being reachable
by unauthenticated network clients:

* token resolution (env / config / generated)
* a request gate that trusts loopback but requires a token otherwise
* ``safe_path`` to confine user-supplied paths to a base directory
"""

import hmac
import os
import secrets

from flask import request, jsonify

# Addresses treated as "on the device itself". Behind a reverse proxy this
# check should be disabled (set ``web.trust_loopback`` to false) because
# ``remote_addr`` would then be the proxy, not the real client.
LOOPBACK_ADDRS = {'127.0.0.1', '::1', 'localhost'}


def resolve_token(config):
    """Resolve the API token, generating a strong one if none is configured.

    Precedence: ``VIVISECT_AUTH_TOKEN`` env var, then ``web.auth_token`` in the
    config file, then a freshly generated token.

    Returns a ``(token, generated)`` tuple so callers can surface a freshly
    generated token to the operator (it is the only way to reach the API
    remotely).
    """
    token = os.environ.get('VIVISECT_AUTH_TOKEN') or (config.get('web.auth_token') or '')
    token = token.strip()
    if token:
        return token, False
    return secrets.token_urlsafe(32), True


def is_loopback(req):
    """Return True if the request originated from the local machine."""
    return (req.remote_addr or '').strip() in LOOPBACK_ADDRS


def extract_token(req):
    """Pull a caller-supplied token from the standard locations.

    Accepts an ``Authorization: Bearer`` header, an ``X-Auth-Token`` header, or
    a ``token`` query parameter (used for browser download links that cannot
    set headers).
    """
    auth = req.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        return auth[7:].strip()
    header = req.headers.get('X-Auth-Token')
    if header:
        return header.strip()
    return req.args.get('token')


def token_matches(provided, expected):
    """Constant-time comparison of a provided token against the expected one."""
    if not provided or not expected:
        return False
    return hmac.compare_digest(str(provided), str(expected))


def install_auth(app, token, *, trust_loopback=True, exempt_endpoints=()):
    """Register a ``before_request`` gate enforcing the token on the JSON API.

    The index page and static assets stay public so the kiosk UI can load; the
    page bootstraps the token for subsequent API calls. Loopback requests are
    trusted by default so the on-device browser works without a token.
    """
    exempt = set(exempt_endpoints) | {'static', 'index'}

    @app.before_request
    def _check_auth():
        # CORS preflight carries no credentials and must be allowed through.
        if request.method == 'OPTIONS':
            return None
        if request.endpoint in exempt:
            return None
        # The WebSocket handshake cannot set custom headers; authentication for
        # it is enforced in the SocketIO ``connect`` handler instead.
        if request.path.startswith('/socket.io'):
            return None
        if trust_loopback and is_loopback(request):
            return None
        if token_matches(extract_token(request), token):
            return None
        return jsonify({'error': 'Unauthorized'}), 401


def safe_path(base_dir, *paths):
    """Join ``paths`` onto ``base_dir`` and confine the result inside it.

    Returns the resolved absolute path, or ``None`` if the result would escape
    ``base_dir`` (e.g. via ``..`` or an absolute path). Both sides are resolved
    with ``realpath`` so symlinks cannot be used to break out.
    """
    base = os.path.realpath(base_dir)
    target = os.path.realpath(os.path.join(base, *paths))
    if target == base or target.startswith(base + os.sep):
        return target
    return None
