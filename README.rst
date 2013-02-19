===============
managesieve-cli
===============

A command-line client for interacting with ManageSieve servers, fork of
http://pypi.python.org/pypi/managesieve

Installation
------------

At the moment you can install it only via `setup.py`: ::

    # tar zxfv managesieve-cli_0.x.y.tar.gz
    # cd managesieve-cli_0.x.y
    # python setup.py install

Basic Use
---------

To use `managesieve-cli` you must first create a configuration file containing
credentials for accessing the remote ManageSieve server; an example
configuration file is included in the source distribution.

The configuration file is composed by one or more `[account]` section (e.g.
`[account myfreemail]`) that contains the required informations to interact with
the remote ManageSieve server; a nice feature for paranoid people is the
parameter `password_command` which can be specified to obtain the password from
the execution of a third-party program (for example on OS X you could interact
with your `Keychain` via the `security` program, while you could use
`gnome-keyring` on GNU/Linux).

The password to be used during a session can also be passed via standard input,
to make shell scripts users happy :-)

Examples
--------

Use the `list` command to get a list of the remote Sieve scripts; the '*' in
front of a script name indicates the current **active** script: ::

    $ managesieve-cli -c config.cfg -a myaccount list
    test
    vacancy
    * general

To retrieve the `general` script: ::

    $ managesieve-cli -c config.cfg -a myaccount get general > general.sieve

To upload a Sieve script (overwriting an existing one with the same name): ::

    $ managesieve-cli -c config.cfg -a myaccount put -d general general.sieve

Useful resources
----------------

* `A collection of Sieve scripts`_
* `RFC5804`_

.. _A collection of Sieve scripts: http://fastmail.wikia.com/wiki/SieveExamples
.. _RFC5804: http://tools.ietf.org/html/rfc5804

Contributing
------------

Contributions are awesome, github should make it easy.

Credits
-------

* Daniel Kertesz <daniel at spatof dot org>

See `README.old` for a complete list of the original authors; I just rewrote
some code to adapt it to my needs.

.. vim: ft=rst
