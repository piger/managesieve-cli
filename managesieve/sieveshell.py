#!/usr/bin/python
"""
sieveshell - remotely manipulate sieve scripts

SYNOPSIS
       sieveshell [--user=user] [--authname=authname] [--realm=realm]
       [--exec=script] [--auth-mech=mechanism] server

       sieveshell --help

sieveshell allows users to manipulate their scripts on a remote server.
It works via MANAGESIEVE, a work in progress protocol.

Use --help to get a list of the currently supported authentication
mechanisms.

The following commands are recognized:
  list             - list scripts on server
  put <filename> [<target name>]
                   - upload script to server
  get <name> [<filename>]
                   - get script. if no filename display to stdout
  edit <name>      - edit a script, if not existant, create on save
  delete <name>    - delete script.
  activate <name>  - set a script as the active script
  deactivate       - deactivate all scripts
  quit             - quit
"""

__version__ = "0.4"
__author__ = "Hartmut Goebel <h.goebel@crazy-compilers.com>"
__copyright__ = "Copyright (C) 2003-2011 by Hartmut Goebel <h.goebel@crazy-compilers.com>"
__license__ = "GPL"


import sys
import getpass
import inspect
import managesieve
import os
from .utils import read_config_defaults, exec_command


sieve = None

SUPPRESS = '--suppress--' # token for suppressing 'OK' after cmd execution

### the order of functions determines the order for 'help' ###

def cmd_help(cmd=None):
    """help             - this screen (shortcut '?')
help <command>   - help on command"""
    ## output order is the same as the sourcecode order
    if cmd:
        if __command_map.has_key(cmd):
            cmd = __command_map[cmd]
        if __commands.has_key('cmd_%s' % cmd):
            print __commands['cmd_%s' % cmd].__doc__
        else:
            print 'Unknown command', repr(cmd)
            print "Type 'help' for list of commands"
    else:
        cmds = __commands.values()
        cmds.sort(lambda a,b: cmp(a.func_code.co_firstlineno,
                                  b.func_code.co_firstlineno))
        for c in cmds:
            print c.__doc__
    return SUPPRESS

def cmd_list():
    """list             - list scripts on server"""
    res, scripts = sieve.listscripts()
    if res == 'OK':
        for scriptname, active in scripts:
            if active: print scriptname, '\t<<-- active'
            else: print scriptname
        res = SUPPRESS
    return res


def cmd_put(filename, scriptname=None):
    """put <filename> [<target name>]
                 - upload script to server"""
    if not scriptname: scriptname = filename
    try:
        scriptdata = open(filename).read()
    except IOError, e:
        print "Can't read local file %s:" % filename, e.args[1]
        return SUPPRESS
    return sieve.putscript(scriptname, scriptdata)


def cmd_get(scriptname, filename=None):
    """get <name> [<filename>]
                 - get script. if no filename display to stdout"""
    res, scriptdata = sieve.getscript(scriptname)
    if res == 'OK':
        if filename:
            try:
                open(filename, 'w').write(scriptdata)
            except IOError, e:
                print "Can't write local file %s:" % filename, e.args[1]
                return SUPPRESS
        else:
            print scriptdata
            res = SUPPRESS
    return res


def cmd_edit(scriptname):
    """edit <name>      - edit a script, not existant, create on save"""

    def Choice(msg, choices):
        while 1:
            sys.stdout.writelines((msg, ' '))
            answer = sys.stdin.readline().strip()[:1].lower()
            i = choices.find(answer)
            if i >= 0:
                # valid answer
                return i
            # else: continue loop

    def YesNoQuestion(msg):
        # Order 'ny' will return boolen values (y=1)
        return Choice(msg + ' (y/n)', 'ny')

    def SaveToFile(msg, scriptname, tmpname):
        if not YesNoQuestion('%s Save script to file?' % msg):
            return
        scriptname = os.path.join(os.getcwd(), scriptname)
        sys.stdout.write('Enter filename (default %s):' % scriptname)
        filename = sys.stdin.readline().strip()
        if filename == '':
            filename = scriptname
        scriptdata = open(tmpname).read()
        open(filename, 'w').write(scriptdata)

    res, scripts = sieve.listscripts()
    if res != 'OK': return res
    for name, active in scripts:
        if name == scriptname:
            res, scriptdata = sieve.getscript(scriptname)
            if res != 'OK': return res
            break
    else:
        if not YesNoQuestion('Script not on server. Create new?'):
            return 'OK'
        # else: script will be created when saving        
        scriptdata = ''

    import tempfile
    filename = tempfile.mktemp('.siv')
    open(filename, 'w').write(scriptdata)

    editor = os.environ.get('EDITOR', 'vi')
    while 1:
        res = os.system('%s %s' % (editor, filename))
        if res: # error editing
            if not YesNoQuestion('Editor returned failture. Continue?'):
                os.remove(filename)
                return SUPPRESS
            else:
                continue # re-edit
        # else: editing okay
        while 1:
            scriptdata = open(filename).read()
            res = sieve.putscript(scriptname, scriptdata)
            if res == 'OK':
                return res
            # res is NO, BYE
            print res, sieve.response_text or sieve.response_code
            if res == 'NO':
                res = Choice('Upload failed. (E)dit/(R)etry/(A)bort?', 'era')
                if res == 0: break # finish inner loop, return to 'edit'
                elif res == 1: # retry upload
                    continue
                SaveToFile('', scriptname, filename)
            else: # BYE
                SaveToFile('Server closed connection.', scriptname, filename)
            print 'Deleting tempfile.'
            os.remove(filename)
            return SUPPRESS
    raise "Should not come here."

if os.name != 'posix':
    del cmd_edit


def cmd_delete(scriptname):
    """delete <name>    - delete script."""
    return sieve.deletescript(scriptname)
    

def cmd_activate(scriptname):
    """activate <name>  - set a script as the active script"""
    return sieve.setactive(scriptname)


def cmd_deactivate():
    """deactivate       - deactivate all scripts"""
    return sieve.setactive('')


def cmd_quit(*args):
    """quit             - quit"""
    print 'quitting.'
    if sieve:
        try:
            # this mysteriously fails at times
            sieve.logout()
        except:
            pass
    raise SystemExit()


# find all commands (using  introspection)
# NB: edit os only available when running on a posix system
__commands = dict([c
                   for c in inspect.getmembers(sys.modules[__name__],
                                               inspect.isfunction)
                   if c[0].startswith('cmd_')
                  ])

# command aliases/shortcuts
__command_map = {
    '?': 'help',
    'h': 'help',
    'q': 'quit',
    'l': 'list',
    'del': 'delete',
    }


def shell(auth, user=None, passwd=None, realm=None,
          authmech='', server='', use_tls=0, port=managesieve.SIEVE_PORT):
    """Main part"""

    def cmd_loop():
        """Command loop: read and execute lines from stdin."""
        global sieve
        while 1:
            sys.stdout.write('> ')
            line = sys.stdin.readline()
            if not line:
                # EOF/control-d
                cmd_quit()
                break
            line = line.strip()
            if not line: continue
            # todo: parse command line correctly
            line = line.split()
            cmd = __command_map.get(line[0], line[0])
            cmdfunc = __commands.get('cmd_%s' % cmd)
            if not cmdfunc:
                print 'Unknown command', repr(cmd)
            else:
                if __debug__: result = None
                try:
                    result = cmdfunc(*line[1:])
                except TypeError, e:
                    if str(e).startswith('%s() takes' % cmdfunc.__name__):
                        print 'Wrong number of arguments:'
                        print '\t', cmdfunc.__doc__
                        continue
                    else:
                        raise
                assert result != None
                if result == 'OK':
                    print result
                elif result == SUPPRESS:
                    # suppress 'OK' for some commands (list, get)
                    pass
                else:
                    print result, sieve.response_text or sieve.response_code
                    if result == "BYE":
                        # quit when server send BYE
                        cmd_quit()

    global sieve
    try:
        print 'connecting to', server
        try:
            if not auth: auth = getpass.getuser()
            if not user: user = auth
            if not passwd: passwd = getpass.getpass()
        except EOFError:
            # Ctrl-D pressed
            print # clear line
            return
        sieve = managesieve.MANAGESIEVE(server, port=port, use_tls=use_tls)
        print 'Server capabilities:',
        for c in sieve.capabilities: print c,
        print
        try:
            if not authmech:
                # auto-select best method available
                res = sieve.login(authmech, user, passwd)
            elif authmech.upper() == 'LOGIN':
                # LOGIN does not support authenticator
                res = sieve.authenticate(authmech, user, passwd)
            else:
                res = sieve.authenticate(authmech, auth, user, passwd)
        except sieve.error, e:
            print "Authenticate error: %s" % e
            cmd_quit()
        if res != 'OK':
            print res, sieve.response_text or sieve.response_code
            cmd_quit()
        cmd_loop()
    except KeyboardInterrupt:
        print
        cmd_quit()


def main():
    """Parse options and call interactive shell."""
    try:
        from optparse import OptionParser
    except ImportError:
        from optik import OptionParser
    parser = OptionParser('Usage: %prog [options] server')
    parser.add_option('--authname',
                      help= "The user to use for authentication "
                            "(defaults to current user).")
    parser.add_option('--user', dest='username',
                      help = "The authorization name to request; "
                             "by default, derived from the "
                             "authentication credentials.")
    parser.add_option('--passwd', help = "The password to use.")
    parser.add_option('--realm',
                      help= "The realm to attempt authentication in.")
    parser.add_option('--auth-mech', default="",
                      help= "The SASL authentication mechanism to use "
                            "(default: auto select; available: %s)." %  ', '.join(managesieve.AUTHMECHS))
    parser.add_option('--script', '--script-file',
                      help= "Instead of working interactively, run "
                            "commands from SCRIPT, and exit when done.")
    parser.add_option('--use-tls', '--tls', action="store_true",
                      help="Switch to TLS if server supports it.")
    parser.add_option('--port', type="int", default=managesieve.SIEVE_PORT,
                      help="port number to connect to (default: %default)")
    parser.add_option('-v', '--verbose', action='count', default=0,
                      help='Be verbose. May be given several times to increase verbosity')
    parser.add_option('-x', '--password-command', dest='password_command',
                      help="Shell command to execute to get the password")

    config_file = os.environ.get("MANAGESIEVE_CONFIG")
    if config_file:
        read_config_defaults(config_file, parser)

    options, args = parser.parse_args()

    # handle password-command
    if options.password_command:
        options.passwd = exec_command(options.password_command)

    if options.auth_mech and not options.auth_mech.upper() in managesieve.AUTHMECHS:
        parser.error("Authentication mechanism %s is not supported. Choose one of %s" % (options.auth_mech.upper(), ', '.join(managesieve.AUTHMECHS)))

    if len(args) != 1:
        parser.error("Argument 'server' missing.")
    server = args[0]

    if options.verbose:
        level = managesieve.INFO
        if options.verbose > 1:
            level = managesieve.DEBUG0 - (options.verbose-2)
        import logging
        logging.basicConfig(level=level, format="%(message)s")

    shell(options.authname, options.username, options.passwd,
          options.realm, options.auth_mech, server, options.use_tls,
          options.port)
    return 0


if __name__ == "__main__":
    if __doc__ is None:
        raise SystemExit('Must not be run with Python option -OO (removed doc-strings)')
    raise SystemExit(main())
