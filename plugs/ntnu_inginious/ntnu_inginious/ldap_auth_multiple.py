# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS
# files for more information about the licensing of this file.

""" LDAP plugin """

import logging
import ldap3
import flask

from flask import redirect, render_template

from inginious.frontend.pages.social import AuthenticationPage
from inginious.frontend.user_manager import AuthMethod

logger = logging.getLogger("inginious.webapp.plugin.auth.ldap")

import os
PATH_TO_PLUGIN = os.path.abspath(os.path.dirname(__file__))
TEMPLATES_PATH = PATH_TO_PLUGIN + "/templates"

# PATH_TO_PLUGIN = os.path.abspath(os.path.dirname(__file__))
# TEMPLATE_FOLDER = os.path.join(PATH_TO_PLUGIN, "templates")


class LdapAuthMethod(AuthMethod):
    """
    LDAP auth method
    """

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
            return (
                '<img src="'
                + self._imlink
                + '" style="-moz-user-select: none; -webkit-user-select: none;'
                ' user-select: none; max-width: 50px; max-height:50px;" />'
            )
        else:
            return (
                '<i class="fa fa-address-book" style="font-size:50px; '
                'color:#000000;"></i>'
            )

    def get_auth_link(self, auth_storage, share=False):
        return flask.request.url_root + "auth/page/" + self._id

    def callback(self, auth_storage):
        return None

    def share(self, auth_storage, course, task, submission, language):
        return False

    def allow_share(self):
        return False

    def get_settings(self):
        return self._settings


class LDAPAuthenticationPage(AuthenticationPage):
    def GET(self, id):
        settings = self.user_manager.get_auth_method(id).get_settings()
        return self.render_helper(settings)

    def POST(self, id):
        # Get configuration
        settings = self.user_manager.get_auth_method(id).get_settings()
        login_data = flask.request.form
        login = login_data["login"].strip().lower()
        password = login_data["password"]

        # do not send empty password to the LDAP
        if password.rstrip() == "":
            return self.render_helper(settings, error=_("Empty password"))
        try:
            # Connect to the ldap
            logger.debug(f"Connecting to {settings['host']}:{settings['port']}")

            # print(settings['host'], settings['port'])
            # print(settings["base_dn"], request)
            # at.ntnu.no None
            # dc=ntnu,dc=no (uid=daniesso)
            conn = ldap3.Connection(
                ldap3.Server(
                    settings["host"],
                    port=settings["port"],
                    use_ssl=settings["encryption"] == "ssl",
                    get_info=ldap3.ALL,
                ),
                auto_bind=True,
            )
            logger.debug(
                "Connected to "
                + settings["host"]
                + ", port "
                + str(settings["port"])
            )
        except Exception as e:
            logger.exception(f"Can't initialize connection to {settings['host']}: {str(e)}")
            return self.render_helper(settings, error=_("Cannot contact host"))
        try:
            request = settings["request"].format(login)
            conn.search(
                settings["base_dn"], request, attributes=["cn", "mail"]
            )
            user_datas = conn.response
        except Exception as ex:
            logger.exception(f"Can't get user data : {str(ex)}")
            conn.unbind()
            return self.render_helper(settings, _("Unknown user"))

        username = None
        email = None
        realname = None

        for index, user_data in enumerate(user_datas):
            if conn.rebind(user_data["dn"], password=password):
                try:
                    username = login
                    realname = user_data["attributes"][
                        settings.get("cn", "cn")
                    ][0]
                    email = user_data["attributes"][
                        settings.get("mail", "mail")
                    ][0]
                    break
                except KeyError as e:
                    logger.info(
                        "Attempt %d/%d: Can't get field "
                        % (index + 1, len(user_datas))
                        + str(e)
                        + " from your LDAP server"
                    )
                except Exception as e:
                    logger.info(
                        "Attempt %d/%d: Can't get some user fields"
                        % (index + 1, len(user_datas))
                    )

            else:
                logger.debug("Ldap Auth feilet (feil passord)")
                conn.unbind()
                return self.render_helper(settings, _("Incorrect password"))

        if username is None:
            logger.debug(
                "Login feilet. Ingen username=%s returnert fra LDAP søk"
                % login
            )
            return self.render_helper(settings, "Fant ingen brukere med det brukernavnet ved NTNU")
        elif realname is None:
            logger.debug(
                "Fant username=%s, men det var ingen tilknyttede navn"
                % username
            )
            return self.render_helper(settings, "Kunne ikke finne navnet ditt i NTNUs system")
        logger.debug(
            "Suksessfullt logget inn med (username=%s, realname=%s, email=%s)"
            " etter %d LDAP-iterasjoner"
            % (username, realname, email, index + 1)
        )

        if email is None:
            email = "{0}@stud.ntnu.no".format(username)

        conn.unbind()

        if not self.user_manager.bind_user(id, (username, realname, email, {})):
            return redirect(flask.request.url_root + "signin?binderror")

        # INGInious does not set the username in the profile of the
        # user to the authentication method username when an external
        # authentication service is used. Still, the user must have a
        # username that is neither None nor an empty string. Thus,
        # INGInious will force the user to set their username after the
        # first login. We want this username to be the NTNU username
        # and thus set this ourselves, if not already set.
        current_username = self.user_manager.session_username()
        if current_username is None or current_username == "":
            logger.debug(
                f"Brukeren med NTNU-brukernavnet {username}' har ikke noen "
                "brukernavn knyttet til sin konto. Knytter NTNU-brukernavnet "
                "til kontoen."
            )

            user_profile = {"username": username, "realname": realname, "email": email,
                            "language": self.user_manager.session_language(),
                            "bindings": {"ntnu": [username, {}]}, "language": self.user_manager.session_language(),
                            "code_indentation": self.user_manager.session_code_indentation(), "tos_accepted": False}

            self.user_manager.connect_user(user_profile)

        auth_storage = self.user_manager.session_auth_storage().setdefault(
            id, {}
        )
        return redirect(auth_storage.get("redir_url", flask.request.url_root))

    def render_helper(self, settings, error=False):
        return render_template("ldap_auth_ntnu/custom_auth_form.html",
                template_folder="frontend/plugins/auth", settings=settings,
                error=error)


def init(plugin_manager, _2, conf):
    """
    Allow to connect through a LDAP service

    Available configuration:
    ::

        plugins:
            - plugin_module": "inginious.frontend.plugins.auth.ldap_auth",

              host: "ldap.test.be",
              port: 0,
              encryption: "ssl",
              base_dn: "o=test,c=be",
              request: "(uid={})",
              name: "LDAP Login"

    *host*
        The host of the ldap server
    *encryption*
        Encryption method used to connect to the LDAP server
        Can be either "none", "ssl" or "tls"
    *request*
        Request made to the server in order to find the dn of the
        user. The characters "{}" will be replaced by the login
        name.

    """

    encryption = conf.get("encryption", "none")
    if encryption not in ["none", "ssl", "tls"]:
        raise Exception(f"Unknown encryption method {encryption}")
    if encryption == "none":
        conf["encryption"] = None

    if conf.get("port", 0) == 0:
        conf["port"] = None

    the_method = LdapAuthMethod(
        conf.get("id"), conf.get("name", "LDAP"), conf.get("imlink", ""), conf
    )
    plugin_manager.add_page(r"/auth/page/<id>",
            LDAPAuthenticationPage.as_view("ldapauthenticationpage"))
    plugin_manager.register_auth_method(the_method)

    plugin_manager.add_template_prefix("ldap_auth_ntnu", TEMPLATES_PATH)

