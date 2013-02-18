# -*- coding: utf-8 -*-
import argparse
import logging
from pprint import pprint
from config import parse_config_file
from utils import exec_command
from .mio import ManageSieveClient


log = logging.getLogger(__name__)


def parse_cmdline():
    description = ("managesieve-cli is a command-line utility for "
                   "interacting with remote managesieve servers")
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-c', '--config', required=True)
    parser.add_argument('-a', '--account', required=True)
    parser.add_argument('--debug', action="store_true",
                        help="Print debugging informations")

    subparsers = parser.add_subparsers(help="sub-command help")
    cmd_list = subparsers.add_parser("list", help="list command")
    cmd_list.set_defaults(cmd="list")

    cmd_put = subparsers.add_parser("put", help="put command")
    cmd_put.add_argument('-d', '--destfile', help="dest file")
    cmd_put.set_defaults(cmd="put")

    cmd_get = subparsers.add_parser("get", help="get command")
    cmd_get.add_argument('name', metavar='SCRIPT-NAME',
                         help="Name of the remote script")
    cmd_get.add_argument('-d', '--destfile', help="dest file")
    cmd_get.set_defaults(cmd="get")

    cmd_edit = subparsers.add_parser("edit", help="edit command")
    cmd_edit.set_defaults(cmd="edit")

    cmd_activate = subparsers.add_parser("activate", help="activate command")
    cmd_activate.set_defaults(cmd="activate")

    cmd_deactivate = subparsers.add_parser("deactivate", help="deactivate command")
    cmd_deactivate.set_defaults(cmd="deactivate")

    cmd_delete = subparsers.add_parser("delete", help="delete command")
    cmd_delete.set_defaults(cmd="delete")

    args = parser.parse_args()

    return args


def cmd_list(args, sieve):
    scripts = sieve.list_scripts()

    for script, active in scripts:
        print "%s%s" % ('* ' if active else '', script)


def cmd_get(args, sieve):
    data = sieve.get_script(args.name)
    print data


def run_command(args, config, account_config):
    use_tls = True if account_config.get('remote.use_tls') else False
    address = account_config.get('remote.host')
    port = int(account_config.get('remote.port'))

    sieve = ManageSieveClient(address, port, use_tls=use_tls)
    sieve.connect()

    username = account_config.get('remote.user')
    auth_mech = account_config.get('remote.auth', '')
    auth_name = account_config.get('remote.auth_name', None)
    password_command = account_config.get('remote.password_command')
    if password_command:
        password = exec_command(password_command)
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

    if args.cmd == "list":
        cmd_list(args, sieve)
    elif args.cmd == "get":
        cmd_get(args, sieve)
    else:
        raise RuntimeError("You must write the code for that command :-P")


def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s: %(message)s [in "
                        "%(funcName)s %(filename)s:%(lineno)d]",
                        datefmt="%H:%M")
    args = parse_cmdline()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    config = parse_config_file(args.config)
    account_config = config.get(args.account)
    if account_config is None:
        print "Account configuration '%s' not found" % args.account

    run_command(args, config, account_config)
