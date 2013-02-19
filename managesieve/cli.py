# -*- coding: utf-8 -*-
"""
    managesieve.cli
    ~~~~~~~~~~~~~~~

    Command line interface to ManageSieveClient instances.

    :copyright: (c) 2013 by Daniel Kertesz <daniel@spatof.org>
    :license: GNU Public License v3 (GPLv3)
"""
from __future__ import with_statement
import os
import sys
import argparse
import logging
import codecs
from pprint import pprint
from config import parse_config_file
from utils import exec_command
from .mio import ManageSieveClient, CommandFailed


log = logging.getLogger(__name__)


def show_error(message):
    sys.stderr.write("%s\n" % message)


class Client(object):
    def __init__(self, args, sieve):
        self.args = args
        self.sieve = sieve

    def run(self):
        fname = "cmd_%s" % self.args.cmd
        if hasattr(self, fname):
            fn = getattr(self, fname)
            try:
                fn()
            except CommandFailed, e:
                show_error("ERROR: %s" % e)
                sys.exit(1)
        else:
            show_error("Invalid or unimplemented command: %s" % self.args.cmd)
            sys.exit(1)
        sys.exit(0)

    def cmd_list(self):
        scripts = self.sieve.list_scripts()

        for script, active in scripts:
            print "%s%s" % ('* ' if active else '',
                            script.encode('utf-8', 'replace'))

    def cmd_get(self):
        script_name = unicode(self.args.name, 'utf-8', 'replace')
        data = self.sieve.get_script(script_name)
        print data.encode('utf-8', 'replace')

    def cmd_put(self):
        if self.args.destfile:
            script_dest = self.args.destfile
        else:
            script_dest = os.path.basename(self.args.name)

        script_dest = unicode(script_dest, 'utf-8', 'replace')
        data = None
        with codecs.open(self.args.name, 'r', 'utf-8') as fd:
            data = fd.read()

        response = self.sieve.put_script(script_dest, data)
        print response.text

    def cmd_activate(self):
        if self.args.name:
            script_name = unicode(self.args.name, 'utf-8', 'replace')
        else:
            script_name = u""
        response = self.sieve.set_active(script_name)
        print response.text

    def cmd_delete(self):
        script_name = unicode(self.args.name, 'utf-8', 'replace')
        response = self.sieve.delete_script(script_name)
        print response.text

    def cmd_rename(self):
        old_name = unicode(self.args.old_name, 'utf-8', 'replace')
        new_name = unicode(self.args.new_name, 'utf-8', 'replace')
        response = self.sieve.rename_script(old_name, new_name)
        print response.text

    def cmd_have_space(self):
        script_name = unicode(self.args.name, 'utf-8', 'replace')
        size = os.path.getsize(self.args.name)
        response = self.sieve.have_space(script_name, size)
        if response.is_ok:
            print "Server can accept %s: %s" % (self.args.name, response.text)
        else:
            print "Server does not have space for %s: %s" % (
                self.args.name, response.text)

    def cmd_capability(self):
        response = self.sieve.capability()
        if response.is_ok:
            capabilities = response.data
            for cap in capabilities:
                print ': '.join(cap[0:2])
        else:
            print "Command failed: %s" % response.text


def parse_cmdline():
    description = ("A command-line utility for interacting with remote "
                   "managesieve servers")
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-c', '--config', required=True, metavar='FILENAME',
                        help="Specify a configuration file")
    parser.add_argument('-a', '--account', required=True, metavar='NAME',
                        help="Specify an account name from the " \
                        "configuration file")
    parser.add_argument('--debug', action="store_true",
                        help="Print debug output (verbose)")
    parser.add_argument('-v', '--verbose', action="store_true",
                        help="Show more output")

    subparsers = parser.add_subparsers(help="The sub-command to execute")
    cmd_list = subparsers.add_parser(
        "list",
        description="List the remote Sieve scripts",
        help="Return a list of remote Sieve scripts")
    cmd_list.set_defaults(cmd="list")

    cmd_put = subparsers.add_parser(
        "put",
        description="Upload a Sieve script to the remote server",
        help="Upload a Sieve script to the remote server")
    cmd_put.add_argument('name', metavar='SCRIPT-NAME',
                         help="Absolute path to the file to be uploaded")
    cmd_put.add_argument('-d', '--destfile', help="dest file")
    cmd_put.set_defaults(cmd="put")

    cmd_get = subparsers.add_parser(
        "get",
        description="Retrieve a Sieve script from the remote server",
        help="Retrieve a Sieve script from the remote server")
    cmd_get.add_argument('name', metavar='SCRIPT-NAME',
                         help="Name of the remote script")
    cmd_get.set_defaults(cmd="get")

    cmd_activate = subparsers.add_parser(
        "activate",
        description="Activate a remote Sieve script or deactivate " \
        "the current active script",
        help="Activate a remote Sieve script")
    cmd_activate.add_argument(
        'name', metavar='SCRIPT-NAME', nargs='?',
        help="Name of the remote script; can be omitted to deactivate " \
        "the current active script")
    cmd_activate.set_defaults(cmd="activate")

    cmd_delete = subparsers.add_parser(
        "delete",
        description="Delete a remote Sieve script",
        help="Delete a remote Sieve script")
    cmd_delete.add_argument('name', metavar='SCRIPT-NAME',
                            help="Name of the remote script to delete")
    cmd_delete.set_defaults(cmd="delete")

    cmd_rename = subparsers.add_parser(
        "rename",
        description="Rename a remote Sieve script",
        help="Rename a remote Sieve script")
    cmd_rename.add_argument("old_name", metavar="SCRIPT-NAME",
                            help="Name of the Sieve script to be renamed")
    cmd_rename.add_argument("new_name", metavar="DESTINATION",
                            help="Destination name")
    cmd_rename.set_defaults(cmd="rename")

    cmd_havespace = subparsers.add_parser(
        "have_space",
        description="Check if the quota on the remote server permits " \
        "the upload of a Sieve script",
        help="Peform a HAVESPACE command for a local Sieve script")
    cmd_havespace.add_argument("name", metavar="FILENAME",
                               help="Absolute path of a local Sieve script")
    cmd_havespace.set_defaults(cmd="have_space")

    cmd_capabilities = subparsers.add_parser(
        "capability",
        description="Request the server capability list",
        help="Request the server capability list")
    cmd_capabilities.set_defaults(cmd="capability")

    args = parser.parse_args()
    return args


def run_command(args, config):
    general_config = config.get('general')
    account_config = config.get(args.account)
    if account_config is None:
        show_error("Account configuration '%s' not found" % args.account)
        sys.exit(1)

    use_tls = True if account_config.get('remote.use_tls') else False
    address = account_config.get('remote.host')
    port = int(account_config.get('remote.port'))

    sieve = ManageSieveClient(address, port, use_tls=use_tls)
    sieve.connect()

    username = account_config.get('remote.user')
    auth_mech = account_config.get('remote.auth', '')
    auth_name = account_config.get('remote.auth_name', None)

    general_password = general_config.get('password')
    password_command = account_config.get('remote.password_command')

    # Use the password submitted via stdin if present
    if general_password:
        password = general_password

    # Try to execute the password command
    elif password_command:
        password = exec_command(password_command)

    # Get the password from the config file
    else:
        password = account_config.get('remote.password')

    try:
        if not auth_mech:
            res = sieve.login(auth_mech, username, password)

        elif auth_mech == 'LOGIN':
            res = sieve.authenticate(auth_mech, username, password)
        else:
            res = sieve.authenticate(auth_mech, auth_name, username, password)
    except Exception, e:
        raise

    client = Client(args, sieve)
    client.run()


def handle_stdin():
    if not sys.stdin.isatty():
        line = sys.stdin.readline()
        return line.rstrip("\n")
    else:
        return None


def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s: %(message)s [in "
                        "%(funcName)s %(filename)s:%(lineno)d]",
                        datefmt="%H:%M")
    args = parse_cmdline()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    config = parse_config_file(args.config)
    stdin_pw = handle_stdin()
    if stdin_pw:
        config['general']['password'] = stdin_pw

    run_command(args, config)
