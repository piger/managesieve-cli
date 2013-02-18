# -*- coding: utf-8 -*-
"""
% nc spatof.org 4190
"IMPLEMENTATION" "dovecot"
"SIEVE" "fileinto reject envelope encoded-character vacation subaddress comparator-i;ascii-numeric relational regex imap4flags copy include variables body enotify environment mailbox date"
"SASL" " DIGEST-MD5 CRAM-MD5"
"STARTTLS"
"NOTIFY" "mailto"
"VERSION" "1.0"
OK "Hay!"
ciao
NO "Error in MANAGESIEVE command received by server."
QUIT
NO "Error in MANAGESIEVE command received by server."
^]
NO "Error in MANAGESIEVE command received by server."
^C
[2]    50709 interrupt  nc spatof.org 4190

"""
import shlex
import logging
import socket
import binascii
from pprint import pprint
from . import SSLFakeSocket, SSLFakeFile

try:
    import ssl
    ssl_wrap_socket = ssl.wrap_socket
except ImportError:
    ssl_wrap_socket = socket.ssl


log = logging.getLogger(__name__)


class ManageSieveClientError(Exception): pass
class EOFFromServer(ManageSieveClientError): pass
class InvalidResponse(ManageSieveClientError): pass
class InvalidState(ManageSieveClientError): pass
class ConnectionError(ManageSieveClientError): pass
class CommandFailed(ManageSieveClientError): pass


class Response(object):

    # Response status
    OK = "OK"
    NO = "NO"
    BYE = "BYE"

    def __init__(self, status, code, text, data):
        self.status = status
        self.code = code
        self.text = text
        self.data = data[:]

    def __repr__(self):
        return "<Response(%r, %r, %r, %r)>" % (self.status, self.code,
                                               self.text, self.data)


class ManageSieveClient(object):

    COMMAND_STATES = {
        'STARTTLS': ('NONAUTH',),
        'AUTHENTICATE': ('NONAUTH',),
        'LOGOUT': ('NONAUTH', 'AUTH', 'LOGOUT'),
        'CAPABILITY': ('NONAUTH', 'AUTH'),
        'GETSCRIPT': ('AUTH',),
        'PUTSCRIPT': ('AUTH',),
        'SETACTIVE': ('AUTH',),
        'DELETESCRIPT': ('AUTH',),
        'LISTSCRIPTS': ('AUTH',),
        'HAVESPACE': ('AUTH',),
    }

    AUTH_PLAIN = "PLAIN"
    AUTH_LOGIN = "LOGIN"
    # authentication mechanisms currently supported
    # in order of preference
    AUTHMECHS = [AUTH_PLAIN, AUTH_LOGIN]

    def __init__(self, host, port, use_tls=True, keyfile=None, certfile=None):
        self.host = host
        self.port = port
        self.use_tls = use_tls
        self.keyfile = keyfile
        self.certfile = certfile

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.fd = self.socket.makefile('rw')

        self.state = 'NONAUTH'

        self.capabilities = []
        self.tls_support = False
        self.login_mechs = []
        self.implementation = None


    def connect(self):
        self.socket.connect((self.host, self.port))
        log.debug("Connected to remote server %s:%d" % (self.host, self.port))
        response = self._read_response()
        if response.status == Response.OK:
            self._parse_capabilities(response.data)

            if self.use_tls and self.tls_support:
                response_tls = self.starttls(self.keyfile, self.certfile)
        else:
            raise InvalidResponse("Server responded with %s, expected OK; %r" %
                                  (response.status, response))

    def authenticate(self, mechanism, *auth_objects):
        mechanism = mechanism.upper()
        if not mechanism in self.login_mechs:
            raise ManageSieveClientError("Server doesn't allow %s "
                                         "authentication" % mechanism)

        if mechanism == self.AUTH_LOGIN:
            auth_objects = [self._sieve_name(binascii.b2a_base64(ao)[:-1])
                            for ao in auth_objects]

        elif mechanism == self.AUTH_PLAIN:
            if len(auth_objects) < 3:
                # assume authorization identity (authzid) is missing
                # and these two authobjects are username and password
                auth_objects.insert(0, '')
            ao = '\0'.join(auth_objects)
            ao = binascii.b2a_base64(ao)[:-1]
            auth_objects = [ self._sieve_string(ao) ]

        else:
            raise ManageSieveClientError("Unsupported authentication: %s" %
                                         mechanism)

        response = self._send_command("AUTHENTICATE",
                                     self._sieve_name(mechanism),
                                     *auth_objects)
        if response.status == Response.OK:
            log.debug("Authenticated")
            self.state = "AUTH"
        else:
            log.error("Authentication failed")

        return response

    def login(self, auth, user, password):
        for mechanism in self.AUTHMECHS:
            if mechanism in self.login_mechs:
                if mechanism == self.AUTH_LOGIN:
                    auth_objects = [user, password]
                else:
                    auth_objects = [auth, user, password]
                return self.authenticate(mechanism, *auth_objects)
        raise ManageSieveClientError("No matching authentication mechanism "
                                     "found")

    def logout(self):
        self._send_command("LOGOUT")
        self.fd.close()
        self.socket.close()

    def starttls(self, keyfile=None, certfile=None):
        response = self._send_command("STARTTLS")
        if response.status == Response.OK:
            ssl_obj = ssl_wrap_socket(self.socket, keyfile, certfile)
            self.socket = SSLFakeSocket(self.socket, ssl_obj)
            self.fd = SSLFakeFile(ssl_obj)
            self._reset_capabilities()

            # qui il server rimanda le capabilities...
            response_tls = self._read_response()
            # ma pare che alcuni server non lo facciano, quindi vanno richieste
            # di nuovo
            self.capability()
            log.debug("Started TLS session")
        else:
            raise InvalidResponse("Server responded %s at STARTTLS command, "
                                  "expected OK; %r" %
                                  (response.status, response))
        return response

    def capability(self):
        response = self._send_command("CAPABILITY")
        if response.status == Response.OK:
            self._parse_capabilities(response.data)
        else:
            raise InvalidResponse("Server responded %s at CAPABILITY command, "
                                  "expected OK; %r" %
                                  (response.status, response))
        return response

    def list_scripts(self):
        response = self._send_command('LISTSCRIPTS')
        if response.status == Response.OK:
            scripts = []
            for token in response.data:
                if not len(token):
                    continue
                script_name = token[0]
                script_active = True if len(token) > 1 else False
                scripts.append((script_name, script_active))
            return scripts
        else:
            raise CommandFailed("LISTSCRIPTS failed: %r" % response)

    def _parse_capabilities(self, capabilities):
        if not capabilities:
            return

        for cap in capabilities:
            if len(cap) >= 2:
                name, value = cap[0:2]
            else:
                name = cap[0]
                value = None

            if name == "IMPLEMENTATION":
                self.implementation = value
            elif name == "SASL":
                self.login_mechs = value.split(' ')
            elif name == "SIEVE":
                self.capabilities = value.split(' ')
            elif name == "STARTTLS":
                self.tls_support = True

        log.debug("Server capabilities: TLS=%r, login mechs=%r, SIEVE "
                  "capabilities=%r, IMPLEMENTATION=%s" %
                  (self.tls_support, self.login_mechs, self.capabilities,
                   self.implementation))

    def _sieve_name(self, name):
        return '"%s"' % name

    def _sieve_string(self, string):
        return '{%d+}\r\n%s' % (len(string), string)

    def _reset_capabilities(self):
        self.implementation = None
        self.login_mechs = []
        self.capabilities = []
        self.tls_support = False
    
    def _read_response(self):
        """
        read: "IMPLEMENTATION" "dovecot"\r\n
        """
        log.debug("Waiting for response")
        lines = []
        while True:
            line = self.fd.readline()
            if not line:
                raise EOFFromServer
            line = line.rstrip("\r\n")
            log.debug("Read line: %r" % line)
            tokens = shlex.split(line)
            if not tokens:
                raise InvalidResponse("Empty tokens from split: %r" % line)

            if tokens[0] in ('OK', 'NO', 'BYE'):
                status = tokens.pop(0)
                code = None
                text = None
                if len(tokens):
                    tok = tokens.pop(0)
                    if tok.startswith('('):
                        code = tok
                        text = tokens
                    else:
                        text = tok
                response = Response(status, code, text, lines)
                log.debug("Returning response %r" % response)
                return response
            else:
                log.debug("Appending tokens %r" % (tokens,))
                lines.append(tuple(tokens))

    def _send_command(self, name, arg1=None, arg2=None, *options):
        if self.state not in self.COMMAND_STATES[name]:
            raise InvalidState("Command %s illegal in state %s" %
                               (name, self.state))
        line = ' '.join(filter(None, (name, arg1, arg2)))
        log.debug("Sending command: %r" % line)
        try:
            self.socket.send("%s\r\n" % line)
            for option in options:
                log.debug("Sending option: %s" % option)
                self.socket.send("%s\r\n" % option)
            response = self._read_response()
        except (socket.error, OSError), e:
            raise ConnectionError("Socket error: %s" % e)
        return response


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s %(levelname)s: %(message)s [in "
                        "%(funcName)s %(filename)s:%(lineno)d]",
                        datefmt="%H:%M")
    m = ManageSieveClient('spatof.org', 4190)
    m.connect()
    m.logout()
