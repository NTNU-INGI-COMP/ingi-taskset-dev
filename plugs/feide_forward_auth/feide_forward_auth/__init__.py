# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS
# files for more information about the licensing of this file.

""" Feide forward-auth plugin.

Trusts the identity headers set by oauth2-proxy, which runs as a Traefik
forward-auth middleware in front of INGInious. Once the proxy has authenticated
a user with Feide (OIDC), every request to INGInious carries ``X-Auth-Request-*``
headers. This plugin turns those headers into an INGInious session, creating the
account on first sight. There is no password flow -- authentication already
happened at the proxy.

Two entry points share the same login logic:

* a Flask ``before_request`` hook that logs the user in transparently on the
  first page navigation (seamless SSO); and
* a ``Feide`` auth method + ``/auth/feide/<id>`` page, so the sign-in page still
  offers a manual button and the standard redir_url flow keeps working.
"""

import base64
import json
import logging
from urllib.parse import quote

import flask
from flask import current_app, redirect, session, url_for

from inginious.frontend.models import User
from inginious.frontend.user_manager import AuthMethod, UserManager
from inginious.frontend.pages.utils import INGIniousPage

logger = logging.getLogger("inginious.webapp.plugin.auth.feide")

# The auto-login hook must never touch these paths: static assets (needless DB
# work), the auth pages themselves and logout (would defeat signing out).
_SKIP_PREFIXES = ("/static", "/auth/", "/logout")


def _header(name):
    """Return a stripped, non-empty request header value, or None."""
    if not name:
        return None
    val = flask.request.headers.get(name)
    if val is not None:
        val = val.strip()
    return val or None


def _decode_jwt_claims(token):
    """Decode a JWT payload without verifying the signature.

    The token reaches us as ``Authorization: Bearer <id_token>`` set by
    oauth2-proxy over the trusted internal network, so the proxy has already
    verified it; we only need to read the claims.
    """
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)  # restore base64 padding
        return json.loads(base64.urlsafe_b64decode(payload.encode("ascii")))
    except Exception:
        logger.debug("Feide forward-auth: could not decode id_token", exc_info=True)
        return {}


def _id_token_claims():
    """Claims from the id_token in the Authorization header, or ``{}``."""
    auth = flask.request.headers.get("Authorization", "")
    if auth[:7].lower() == "bearer ":
        return _decode_jwt_claims(auth[7:].strip())
    return {}


def _claim_str(value):
    """Coerce a claim to a clean string.

    Feide returns some claims (e.g. ``cn``) LDAP-style as a list; take the first
    non-empty element in that case.
    """
    if isinstance(value, (list, tuple)):
        value = next((v for v in value if v), None)
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _full_name(claims):
    """Best-effort display name from OIDC name claims."""
    given = _claim_str(claims.get("given_name")) or ""
    family = _claim_str(claims.get("family_name")) or ""
    joined = (given + " " + family).strip()
    return joined or None


def _identity(settings):
    """Extract ``(username, realname, email)`` for the current request, or None.

    The email is mandatory: without it we cannot key an account. The display
    name comes from the id_token ``name`` claim (the ``X-Auth-Request-User``
    header is Feide's opaque ``sub`` UUID and must never become the realname);
    the fallback chain degrades to the username, never to the UUID.
    """
    claims = _id_token_claims() if settings.get("use_id_token", True) else {}

    email = _header(settings["email_header"]) or _claim_str(claims.get("email"))
    if not email:
        return None

    username = _header(settings["username_header"]) or _claim_str(claims.get("preferred_username"))
    if not username:
        # No preferred-username claim: fall back to the email local part.
        username = email.split("@")[0]

    realname = (_claim_str(claims.get(settings.get("name_claim", "name")))
                or _full_name(claims)
                or username)
    return username, realname, email


def _login(user_manager, auth_id, identity):
    """Bind/log-in the user described by ``identity``. Returns True on success."""
    username, realname, email = identity
    sane_email = UserManager.sanitize_email(email)
    if sane_email is None:
        logger.warning("Feide forward-auth: rejecting invalid email %r", email)
        return False

    # bind_user creates the account (with an empty username) on first login and
    # opens the session; on later logins it just connects the existing account.
    if not user_manager.bind_user(auth_id, (username, realname, sane_email, {})):
        return False

    # INGInious creates externally-authenticated accounts with an empty username
    # and would otherwise prompt the user to pick one. Force it to the Feide
    # username so login stays unattended.
    if not getattr(session, "username", ""):
        User.objects(email=sane_email).update(username=username, realname=realname)
        session.username = username
        session.realname = realname
    return True


class FeideAuthMethod(AuthMethod):
    """Feide auth method, shown as a button on the sign-in page."""

    def __init__(self, id, name, imlink, settings):
        self._id = id
        self._name = name
        self._imlink = imlink
        self._settings = settings

    def get_id(self):
        return self._id

    def get_name(self):
        return self._name

    def get_imlink(self):
        if self._imlink:
            return ('<img src="' + self._imlink + '" style="-moz-user-select: none;'
                    ' -webkit-user-select: none; user-select: none; max-width: 50px;'
                    ' max-height:50px;" />')
        return '<i class="fa fa-university" style="font-size:50px; color:#000000;"></i>'

    def get_auth_link(self, auth_storage, share=False):
        # Core /auth/signin/<id> stores redir_url then redirects here.
        return url_for("feideauthpage", auth_id=self._id)

    def callback(self, auth_storage):
        return None

    def share(self, auth_storage, course, task, submission, language):
        return False

    def allow_share(self):
        return False

    def get_settings(self):
        return self._settings


class FeideAuthPage(INGIniousPage):
    """Manual entry point reached from the sign-in page button."""

    def _handle(self, auth_id):
        auth_method = self.user_manager.get_auth_method(auth_id)
        if not auth_method:
            raise current_app.notfound(message="Auth method doesn't exist.")

        identity = _identity(auth_method.get_settings())
        if identity is None:
            logger.warning("Feide forward-auth: no identity headers on /auth/feide/%s", auth_id)
            return redirect(url_for("signinpage", callbackerror=""))

        if not _login(self.user_manager, auth_id, identity):
            return redirect(url_for("signinpage", binderror=""))

        auth_storage = session.auth_storage.setdefault(auth_id, {})
        return redirect(auth_storage.get("redir_url", "/"))

    def GET(self, auth_id):
        return self._handle(auth_id)

    def POST(self, auth_id):
        return self._handle(auth_id)


def _register_logout(flask_app, user_manager, logout_url, logout_redirect):
    """Intercept INGInious's own ``/logout`` so the existing logout button clears
    all three sessions in one click: the INGInious session, the oauth2-proxy
    cookie, and (via ``rd``) the Feide IdP session.

    ``logout_url``/``logout_redirect`` are absolute site paths/URLs, not
    INGInious-prefixed routes: ``/oauth2/*`` is served by Traefik at the domain
    root, so they must NOT go through ``url_for``.
    """
    target = logout_url
    if logout_redirect:
        # oauth2-proxy clears its cookie then redirects to `rd`; point it at the
        # IdP end-session endpoint for a full logout. `rd` must be a whitelisted
        # domain (OAUTH2_PROXY_WHITELIST_DOMAINS) or oauth2-proxy ignores it.
        target = logout_url + "?rd=" + quote(logout_redirect, safe="")

    @flask_app.before_request
    def feide_logout():
        # request.path is app-relative (SCRIPT_NAME stripped), so INGInious's
        # own logout route is exactly "/logout".
        if flask.request.path.rstrip("/") != "/logout":
            return None
        try:
            user_manager.disconnect_user()  # clears the INGInious session
        except Exception:
            logger.exception("Feide forward-auth: disconnect failed during logout")
        return redirect(target)


def _register_auto_login(flask_app, user_manager, auth_id, settings):
    """Register the seamless before_request auto-login hook."""

    @flask_app.before_request
    def feide_auto_login():
        if getattr(session, "loggedin", False):
            return None
        if flask.request.method != "GET":
            return None
        path = flask.request.path or "/"
        if path.startswith(_SKIP_PREFIXES):
            return None
        # Only act on real page navigations, not asset or XHR requests, so a
        # single page load does not fan out into many login attempts.
        if "text/html" not in flask.request.headers.get("Accept", ""):
            return None
        identity = _identity(settings)
        if identity is None:
            return None
        try:
            _login(user_manager, auth_id, identity)
        except Exception:
            logger.exception("Feide forward-auth: auto-login failed")
        # Return None so the request continues, now with an open session.
        return None


def init(plugin_manager, _client, conf):
    """
    Log users in from oauth2-proxy / Feide forward-auth headers.

    Available configuration::

        plugins:
          - plugin_module: feide_forward_auth
            id: feide
            name: "Feide"
            # Headers set by oauth2-proxy (OAUTH2_PROXY_SET_XAUTHREQUEST=true).
            username_header: "X-Auth-Request-Preferred-Username"
            email_header: "X-Auth-Request-Email"
            # Display name comes from the id_token (Authorization: Bearer),
            # since no X-Auth-Request-* header carries a human name.
            use_id_token: true
            name_claim: "name"
            # Seamless login on first navigation. Disable to require the button.
            auto_login: true
            # Logout: intercepts INGInious's /logout to clear the session then
            # chain to oauth2-proxy sign-out and (via rd) the Feide end-session.
            logout_url: "/oauth2/sign_out"
            logout_redirect: "https://auth.dataporten.no/openid/endsession"

    *username_header*
        Header whose value becomes the INGInious username. Falls back to the
        id_token ``preferred_username`` claim, then the email local part.
    *email_header*
        Header carrying the user email (mandatory; keys the account).
    *use_id_token*
        Decode the id_token from the Authorization header for the display name
        (and email/username fallbacks). Requires oauth2-proxy
        ``OAUTH2_PROXY_SET_AUTHORIZATION_HEADER=true``.
    *name_claim*
        id_token claim used for the display name (default ``name``); may be
        list-valued. Falls back to ``given_name``/``family_name``, then the
        username. Never the ``sub`` UUID carried by ``X-Auth-Request-User``.
    *logout_url*
        oauth2-proxy sign-out path (domain-root, not INGInious-prefixed).
    *logout_redirect*
        ``rd`` target after sign-out; set to the IdP end-session endpoint for a
        full logout, or empty for an app-only logout. The domain must be in
        ``OAUTH2_PROXY_WHITELIST_DOMAINS`` or oauth2-proxy ignores it.
    """
    settings = {
        "username_header": conf.get("username_header", "X-Auth-Request-Preferred-Username"),
        "email_header": conf.get("email_header", "X-Auth-Request-Email"),
        "use_id_token": conf.get("use_id_token", True),
        "name_claim": conf.get("name_claim", "name"),
    }
    auth_id = conf.get("id", "feide")
    name = conf.get("name", "Feide")

    method = FeideAuthMethod(auth_id, name, conf.get("imlink", ""), settings)
    plugin_manager.register_auth_method(method)
    plugin_manager.add_page(r"/auth/feide/<auth_id>", FeideAuthPage.as_view("feideauthpage"))

    # Full logout: the existing /logout button clears the INGInious session,
    # then oauth2-proxy + the Feide IdP session.
    _register_logout(
        plugin_manager._flask_app,
        plugin_manager.get_user_manager(),
        conf.get("logout_url", "/oauth2/sign_out"),
        conf.get("logout_redirect", "https://auth.dataporten.no/openid/endsession"),
    )

    if conf.get("auto_login", True):
        _register_auto_login(plugin_manager._flask_app, plugin_manager.get_user_manager(),
                             auth_id, settings)

    logger.info("Feide forward-auth plugin loaded (id=%s, auto_login=%s)",
                auth_id, conf.get("auto_login", True))
