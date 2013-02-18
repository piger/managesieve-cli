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
from pprint import pprint

try:
    import ssl
    ssl_wrap_socket = ssl.wrap_socket
except ImportError:
    ssl_wrap_socket = socket.ssl


log = logging.getLogger(__name__)


class ManageSieveClientError(Exception): pass
class EOFFromServer(ManageSieveClientError): pass
class InvalidResponse(ManageSieveClientError): pass


class SSLFakeSocket:
    """A fake socket object that really wraps a SSLObject.
    
    It only supports what is needed in managesieve.
    """
    def __init__(self, realsock, sslobj):
        self.realsock = realsock
        self.sslobj = sslobj

    def send(self, str):
        self.sslobj.write(str)
        return len(str)

    sendall = send

    def close(self):
        self.realsock.close()


class SSLFakeFile:
    """A fake file like object that really wraps a SSLObject.

    It only supports what is needed in managesieve.
    """
    def __init__(self, sslobj):
        self.sslobj = sslobj

    def readline(self):
        str = ""
        chr = None
        while chr != "\n":
            chr = self.sslobj.read(1)
            str += chr
        return str

    def read(self, size=0):
        if size == 0:
            return ''
        else:
            return self.sslobj.read(size)

    def close(self):
        pass


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
        response = self.read_response()
        if response.status == Response.OK:
            self._parse_capabilities(response.data)

            if self.use_tls and self.tls_support:
                response_tls = self.starttls(self.keyfile, self.certfile)
        else:
            raise InvalidResponse("Server responded with %s, expected OK; %r" %
                                  (response.status, response))

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

        log.info("New capabilities: TLS=%r, login mechs=%r, SIEVE "
                 "capabilities=%r, IMPLEMENTATION=%s" %
                 (self.tls_support, self.login_mechs, self.capabilities,
                  self.implementation))

    def _reset_capabilities(self):
        self.implementation = None
        self.login_mechs = []
        self.capabilities = []
        self.tls_support = False
    
    def read_response(self):
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

    def send_command(self, *args):
        line = ' '.join(args)
        log.debug("Sending command: %r" % line)
        self.socket.send("%s\r\n" % line)
        response = self.read_response()
        return response

    def logout(self):
        self.send_command("LOGOUT")
        self.fd.close()
        self.socket.close()

    def starttls(self, keyfile=None, certfile=None):
        response = self.send_command("STARTTLS")
        if response.status == Response.OK:
            ssl_obj = ssl_wrap_socket(self.socket, keyfile, certfile)
            self.socket = SSLFakeSocket(self.socket, ssl_obj)
            self.fd = SSLFakeFile(ssl_obj)
            self._reset_capabilities()

            # qui il server rimanda le capabilities...
            response_tls = self.read_response()
            # ma pare che alcuni server non lo facciano, quindi vanno richieste
            # di nuovo
            self.capability()
            log.info("Started TLS session")
        else:
            raise InvalidResponse("Server responded %s at STARTTLS command, "
                                  "expected OK; %r" %
                                  (response.status, response))
        return response

    def capability(self):
        response = self.send_command("CAPABILITY")
        if response.status == Response.OK:
            self._parse_capabilities(response.data)
        else:
            raise InvalidResponse("Server responded %s at CAPABILITY command, "
                                  "expected OK; %r" %
                                  (response.status, response))
        return response


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s %(levelname)s: %(message)s [in "
                        "%(funcName)s %(filename)s:%(lineno)d]",
                        datefmt="%H:%M")
    m = ManageSieveClient('spatof.org', 4190)
    m.connect()
    m.logout()
