# -*- coding: utf-8 -*-
"""Sieve management client module

A Protocol for Remotely Managing Sieve Scripts, RFC 5804
"""

__version__ = "0.4.2"
__author__ = """Hartmut Goebel <h.goebel@crazy-compilers.com>
Ulrich Eck <ueck@net-labs.de> April 2001
"""

__copyright__ = "Copyright (C) 2003-2011 by Hartmut Goebel <h.goebel@crazy-compilers.com> and others"
__license__ = "Python-2.0 like"


import re
import logging
import socket
import binascii
try:
    import ssl
    ssl_wrap_socket = ssl.wrap_socket
except ImportError:
    ssl_wrap_socket = socket.ssl


log = logging.getLogger(__name__)

_re_oknobye = re.compile(r'(?P<type>(OK|NO|BYE))'
                     r'( \((?P<code>.*)\))?'
                     r'( (?P<data>.*))?')

# draft-martin-managesieve-04.txt defines the size tag of literals to
# contain a '+' (plus sign) behind the digits, but timsieved does not
# send one. Thus we are less strikt here:
_re_literal = re.compile(r'.*{(?P<size>\d+)\+?}$')
_re_dquote  = re.compile(r'"(([^"\\]|\\.)*)"')
_re_esc_quote = re.compile(r'\\([\\"])')


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


class ManageSieveError(Exception): pass
class ManageSieveAbort(ManageSieveError): pass


class ManageSieve(object):
    """Sieve client class.

    Instantiate with: MANAGESIEVE(host [, port])

        host - host's name (default: localhost)
        port - port number (default: standard Sieve port).
        
        use_tls  - switch to TLS automatically, if server supports
        keyfile  - keyfile to use for TLS (optional)
        certfile - certfile to use for TLS (optional)

    All Sieve commands are supported by methods of the same
    name (in lower-case).

    Each command returns a tuple: (type, [data, ...]) where 'type'
    is usually 'OK' or 'NO', and 'data' is either the text from the
    tagged response, or untagged results from command.

    All arguments to commands are converted to strings, except for
    AUTHENTICATE.
    """
    
    """
    However, the 'password' argument to the LOGIN command is always
    quoted. If you want to avoid having an argument string quoted (eg:
    the 'flags' argument to STORE) then enclose the string in
    parentheses (eg: "(\Deleted)").
    
    Errors raise the exception class <instance>.error("<reason>").
    IMAP4 server errors raise <instance>.abort("<reason>"),
    which is a sub-class of 'error'. Mailbox status changes
    from READ-WRITE to READ-ONLY raise the exception class
    <instance>.readonly("<reason>"), which is a sub-class of 'abort'.

    "error" exceptions imply a program error.
    "abort" exceptions imply the connection should be reset, and
            the command re-tried.
    "readonly" exceptions imply the command should be re-tried.

    Note: to use this module, you must read the RFCs pertaining
    to the IMAP4 protocol, as the semantics of the arguments to
    each IMAP4 command are left to the invoker, not to mention
    the results.
    """

    CRLF = '\r\n'
    SIEVE_PORT = 2000

    OK = 'OK'
    NO = 'NO'
    BYE = 'BYE'

    AUTH_PLAIN = "PLAIN"
    AUTH_LOGIN = "LOGIN"
    # authentication mechanisms currently supported
    # in order of preference
    AUTHMECHS = [AUTH_PLAIN, AUTH_LOGIN]

    # todo: return results or raise exceptions?
    # todo: on result 'BYE' quit immediatly
    # todo: raise exception on 'BYE'?
    
    # Commands
    commands = {
        # name          valid states
        'STARTTLS':     ('NONAUTH',),
        'AUTHENTICATE': ('NONAUTH',),
        'LOGOUT':       ('NONAUTH', 'AUTH', 'LOGOUT'),
        'CAPABILITY':   ('NONAUTH', 'AUTH'),
        'GETSCRIPT':    ('AUTH', ),
        'PUTSCRIPT':    ('AUTH', ),
        'SETACTIVE':    ('AUTH', ),
        'DELETESCRIPT': ('AUTH', ),
        'LISTSCRIPTS':  ('AUTH', ),
        'HAVESPACE':    ('AUTH', ),
    }


    def __clear_knowledge(self):
        """clear/init any knowledge obtained from the server"""
        self.capabilities = []
        self.loginmechs = []
        self.implementation = ''
        self.supports_tls = 0

    def __init__(self, host='', port=SIEVE_PORT,
                 use_tls=False, keyfile=None, certfile=None):
        self.host = host
        self.port = port
        self.state = 'NONAUTH'

        self.response_text = self.response_code = None
        self.__clear_knowledge()
        
        # Open socket to server.
        self._open(host, port)

        log.info('managesieve version %s', __version__)

        # Get server welcome message,
        # request and store CAPABILITY response.
        typ, data = self._get_response()
        if typ == 'OK':
            self._parse_capabilities(data)
        if use_tls and self.supports_tls:
            typ, data = self.starttls(keyfile=keyfile, certfile=certfile)
            if typ == 'OK':
                self._parse_capabilities(data)


    def _sieve_name(self, name):
        # todo: correct quoting
        return '"%s"' % name


    def _sieve_string(self, string):
        return '{%d+}%s%s' % ( len(string), self.CRLF, string )


    def _parse_capabilities(self, lines):
        for line in lines:
            if len(line) == 2:
                typ, data = line
            else:
                assert len(line) == 1, 'Bad Capabilities line: %r' % line
                typ = line[0]
                data = None
            log.debug('%s: %r', typ, data)
            if typ == "IMPLEMENTATION":
                self.implementation = data
            elif typ == "SASL":
                self.loginmechs = data.split()
            elif typ == "SIEVE":
                self.capabilities = data.split()
            elif typ == "STARTTLS":
                self.supports_tls = 1
            else:
                # A client implementation MUST ignore any other
                # capabilities given that it does not understand.
                pass
        return


    def __getattr__(self, attr):
        #    Allow UPPERCASE variants of MANAGESIEVE command methods.
        if self.commands.has_key(attr):
            return getattr(self, attr.lower())
        raise AttributeError("Unknown MANAGESIEVE command: '%s'" % attr)


    #### Private methods ###
    def _open(self, host, port):
        """Setup 'self.sock' and 'self.file'."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        self.file = self.sock.makefile('r')

    def _close(self):
        self.file.close()
        self.sock.close()

    def _read(self, size):
        """Read 'size' bytes from remote."""
	data = ""
	while len(data) < size:
            data += self.file.read(size - len(data))
	return data

    def _readline(self):
        """Read line from remote."""
        return self.file.readline()

    def _send(self, data):
        return self.sock.send(data)

    def _get_line(self):
        line = self._readline()
        if not line:
            raise ManageSieveAbort('socket error: EOF')
        # Protocol mandates all lines terminated by self.CRLF
        line = line[:-2]
        log.debug('< %s', line)
        return line

    def _simple_command(self, *args):
        """Execute a command which does only return status.

        Returns (typ) with
           typ  = response type

        The responce code and text may be found in <instance>.response_code
        and <instance>.response_text, respectivly.
        """
        return self._command(*args)[0] # only return typ, ignore data


    def _command(self, name, arg1=None, arg2=None, *options):
        """
        Returns (typ, data) with
           typ  = response type
           data = list of lists of strings read (only meaningfull if OK)

        The responce code and text may be found in <instance>.response_code
        and <instance>.response_text, respectivly.
        """
        if self.state not in self.commands[name]:
            raise ManageSieveError('Command %s illegal in state %s' %
                                   (name, self.state))
        # concatinate command and arguments (if any)
        data = " ".join(filter(None, (name, arg1, arg2)))
        log.debug('> %s', data)
        try:
            try:
                self._send('%s%s' % (data, self.CRLF))
                for o in options:
                    log.debug('> %r', o)
                    self._send('%s%s' % (o, self.CRLF))
            except (socket.error, OSError), val:
                raise ManageSieveAbort("socket error: %s" % val)
            return self._get_response()
        except ManageSieveAbort, val:
            raise


    def _readstring(self, data):
        if data[0] == ' ': # space -> error
            raise ManageSieveError('Unexpected space: %r' % data)
        elif data[0] == '"': # handle double quote:
            if not self._match(_re_dquote, data):
                raise ManageSieveError('Unmatched quote: %r' % data)
            snippet = self.mo.group(1)
            return _re_esc_quote.sub(r'\1', snippet), data[self.mo.end():]
        elif self._match(_re_literal, data):
            # read a 'literal' string
            size = int(self.mo.group('size'))
            log.debug('read literal size %s', size)
            return self._read(size), self._get_line()
        else:
            data = data.split(' ', 1)
            if len(data) == 1:
                data.append('')
            return data

    def _get_response(self):
        """
        Returns (typ, data) with
           typ  = response type
           data = list of lists of strings read (only meaningfull if OK)

        The responce code and text may be found in <instance>.response_code
        and <instance>.response_text, respectivly.
        """

        """
    response-deletescript = response-oknobye
    response-authenticate = *(string CRLF) (response-oknobye)
    response-capability   = *(string [SP string] CRLF) response-oknobye
    response-listscripts  = *(string [SP "ACTIVE"] CRLF) response-oknobye
    response-oknobye      = ("OK" / "NO" / "BYE") [SP "(" resp-code ")"] [SP string] CRLF
    string                = quoted / literal
    quoted                = <"> *QUOTED-CHAR <">
    literal               = "{" number  "+}" CRLF *OCTET
                            ;; The number represents the number of octets
                            ;; MUST be literal-utf8 except for values

--> a response either starts with a quote-charakter, a left-bracket or
    OK, NO, BYE

"quoted" CRLF
"quoted" SP "quoted" CRLF
{size} CRLF *OCTETS CRLF
{size} CRLF *OCTETS CRLF
[A-Z-]+ CRLF

        """
        data = [] ; dat = None
        resp = self._get_line()
        while 1:
            if self._match(_re_oknobye, resp):
                typ, code, dat = self.mo.group('type','code','data')
                log.debug('%s response: %s %s', typ, code, dat)
                self.response_code = code
                self.response_text = None
                if dat:
                    self.response_text = self._readstring(dat)[0]

                # if server quits here, send code instead of empty data
                if typ == "BYE":
                    return typ, code

                return typ, data
##             elif 0:
##                 dat2 = None
##                 dat, resp = self._readstring(resp)
##                 if resp.startswith(' '):
##                     dat2, resp = self._readstring(resp[1:])
##                 data.append( (dat, dat2))
##                 resp = self._get_line()
            else:
                dat = []
                while 1:
                    dat1, resp = self._readstring(resp)
                    log.debug('read: %r', dat1)
                    log.debug('rest: %r', resp)
                    dat.append(dat1)
                    if not resp.startswith(' '):
                        break
                    resp = resp[1:]
                if len(dat) == 1:
                    dat.append(None)
                data.append(dat)
                resp = self._get_line()
        return ManageSieveError('Should not come here')


    def _match(self, cre, s):
        # Run compiled regular expression match method on 's'.
        # Save result, return success.
        self.mo = cre.match(s)
        if self.mo is not None:
            log.debug("\tmatched '%r' => %r", cre.pattern, self.mo.groups())
        return self.mo is not None


    ### Public methods ###
    def authenticate(self, mechanism, *authobjects):
        """Authenticate command - requires response processing."""
        # command-authenticate  = "AUTHENTICATE" SP auth-type [SP string]  *(CRLF string)
        # response-authenticate = *(string CRLF) (response-oknobye)
        mech = mechanism.upper()
        if not mech in self.loginmechs:
            raise ManageSieveError("Server doesn't allow %s authentication." % mech)

        if mech == self.AUTH_LOGIN:
            authobjects = [ self._sieve_name(self, binascii.b2a_base64(ao)[:-1])
                            for ao in authobjects
                            ]
        elif mech == self.AUTH_PLAIN:
            if len(authobjects) < 3:
                # assume authorization identity (authzid) is missing
                # and these two authobjects are username and password
                authobjects.insert(0, '')
            ao = '\0'.join(authobjects)
            ao = binascii.b2a_base64(ao)[:-1]
            authobjects = [ self._sieve_string(self, ao) ]
        else:
            raise ManageSieveError("managesieve doesn't support %s authentication." % mech)

        typ, data = self._command('AUTHENTICATE',
                                  self._sieve_name(self, mech), *authobjects)
        if typ == 'OK':
            self.state = 'AUTH'
        return typ


    def login(self, auth, user, password):
        """
        Authenticate to the Sieve server using the best mechanism available.
        """
        for authmech in self.AUTHMECHS:
            if authmech in self.loginmechs:
                authobjs = [auth, user, password]
                if authmech == self.AUTH_LOGIN:
                    authobjs = [user, password]
                return self.authenticate(authmech, *authobjs)
        else:
            raise ManageSieveAbort('No matching authentication mechanism found.')

    def logout(self):
        """Terminate connection to server."""
        # command-logout        = "LOGOUT" CRLF
        # response-logout       = response-oknobye
        typ = self._simple_command('LOGOUT')
        self.state = 'LOGOUT'
        self._close()
        return typ


    def listscripts(self):
        """Get a list of scripts on the server.

        (typ, [data]) = <instance>.listscripts()

        if 'typ' is 'OK', 'data' is list of (scriptname, active) tuples.
        """
        # command-listscripts   = "LISTSCRIPTS" CRLF
        # response-listscripts  = *(sieve-name [SP "ACTIVE"] CRLF) response-oknobye
        typ, data = self._command('LISTSCRIPTS')
        if typ != 'OK': return typ, data
        scripts = []
        for dat in data:
            scripts.append( (dat[0], dat[1] is not None ))
        return typ, scripts


    def getscript(self, scriptname):
        """Get a script from the server.

        (typ, scriptdata) = <instance>.getscript(scriptname)

        'scriptdata' is the script data.
        """
        # command-getscript     = "GETSCRIPT" SP sieve-name CRLF
        # response-getscript    = [string CRLF] response-oknobye
        
        typ, data = self._command('GETSCRIPT', self._sieve_name(self, scriptname))
        if typ != 'OK': return typ, data
        if len(data) != 1:
            ManageSieveError('GETSCRIPT returned more than one string/script')
        # todo: decode data?
        return typ, data[0][0]
    

    def putscript(self, scriptname, scriptdata):
        """Put a script onto the server."""
        # command-putscript     = "PUTSCRIPT" SP sieve-name SP string CRLF
        # response-putscript    = response-oknobye
        return self._simple_command('PUTSCRIPT',
                                    self._sieve_name(self, scriptname),
                                    self._sieve_string(self, scriptdata)
                                    )

    def deletescript(self, scriptname):
        """Delete a scripts at the server."""
        # command-deletescript  = "DELETESCRIPT" SP sieve-name CRLF
        # response-deletescript = response-oknobye
        return self._simple_command('DELETESCRIPT', self._sieve_name(self, scriptname))


    def setactive(self, scriptname):
        """Mark a script as the 'active' one."""
        # command-setactive     = "SETACTIVE" SP sieve-name CRLF
        # response-setactive    = response-oknobye
        return self._simple_command('SETACTIVE', self._sieve_name(self, scriptname))


    def havespace(self, scriptname, size):
        # command-havespace     = "HAVESPACE" SP sieve-name SP number CRLF
        # response-havespace    = response-oknobye
        return self._simple_command('HAVESPACE',
                                    self._sieve_name(self, scriptname),
                                    str(size))


    def capability(self):
        """
        Isse a CAPABILITY command and return the result.
        
        As a side-effect, on succes these attributes are (re)set:
                self.implementation
                self.loginmechs
                self.capabilities
                self.supports_tls
        """
        # command-capability    = "CAPABILITY" CRLF
        # response-capability   = *(string [SP string] CRLF) response-oknobye
        typ, data = self._command('CAPABILITY')
        if typ == 'OK':
            self._parse_capabilities(data)
        return typ, data


    def starttls(self, keyfile=None, certfile=None):
        """Puts the connection to the SIEVE server into TLS mode.

        If the server supports TLS, this will encrypt the rest of the SIEVE
        session. If you provide the keyfile and certfile parameters,
        the identity of the SIEVE server and client can be checked. This,
        however, depends on whether the socket module really checks the
        certificates.
        """
        # command-starttls      = "STARTTLS" CRLF
        # response-starttls     = response-oknobye
        typ, data = self._command('STARTTLS')
        if typ == 'OK':
            sslobj = ssl_wrap_socket(self.sock, keyfile, certfile)
            self.sock = SSLFakeSocket(self.sock, sslobj)
            self.file = SSLFakeFile(sslobj)
            # MUST discard knowledge obtained from the server
            self.__clear_knowledge()
            # NB: We did send a BOGUS command here for buggy servers,
            # but RFC 5804 forbids doing this. And it broke with
            # servers following the RFC.
            typ, data = self._get_response()
            # Buggy servers may not advertise capabilities, thus we
            # need to ask.
            self.capability()
            log.info('started Transport Layer Security (TLS)')
        return typ, data
