.. -*- mode: rst ; ispell-local-dictionary: "american" -*-

===============
`managesieve`
===============

-------------------------------------------------------------------------------------------------------------------------------------
A ManageSieve client library for remotely managing Sieve scripts, including an user application (the interactive 'sieveshell').
-------------------------------------------------------------------------------------------------------------------------------------

:Author:  Hartmut Goebel <h.goebel@crazy-compiler.com>
:Version: 0.4.2
:Copyright: GNU Public License v3 (GPLv3)
:Homepage: http://python-managesieve.origo.ethz.ch/

Sieve scripts allow users to filter incoming email on the mail server.
The ManageSieve protocol allows managing Sieve scripts on a remote
mail server. These servers are commonly sealed so users cannot log
into them, yet users must be able to update their scripts on them.
This is what for the "ManageSieve" protocol is. For more information
about the ManageSieve protocol see `the ManageSieve Internet draft
<http://www.ietf.org/internet-drafts/draft-martin-managesieve-07.txt>`_.

This module allows accessing a Sieve-Server for managing Sieve scripts
there. It is accompanied by a simple yet functional user application
'sieveshell'.

Changes since 0.4
~~~~~~~~~~~~~~~~~~~~~
  - fixed short read (thanks to paurkedal for submitting the patch)
  - Use ssl.wrap_socket() instead of deprecated socket.ssl().
    Thanks to Guido Berhoerster for submitting the patch.

Changes since 0.3
~~~~~~~~~~~~~~~~~~~~~
:managesieve:
  - now works with Python 2.3 and later
  - added support for TLS (STARTTLS), special thanks to Gregory Boyce
    for fixing some corner cases here
  - added support for PLAIN authentication
  - use optparse if available instead of optik.
  - API change: login() no longer uses the LOGIN authentication
    mechanism, but has become a convenience function. It uses the best
    mechanism available for authenticating the user.
  - Several Bugfixes, see HISTORY for details.

  Thanks to Tomas 'Skitta' Lindroos, Lorenzo Boccaccia, Alain Spineux,
  darkness and Gregory Boyce for sending patches.

:sieveshell:
  - added support for different authentication mechanisms
  - added option --start-tls
  - several other enhancements and bugfixes


Requirements and Installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`managesieve` requires

* `Python 2.x`__ or higher (tested with 2.5 and 2.6, but other
  versions should work, too, Python 3.x is *not* supported),
* `logging`__ when using Python < 2.3 (`logging` is already
  included in Python 2.3 and higher)
* `setuptools`__ or `distribute`__ for installation (see below)

__ http://www.python.org/download/
__ http://pypi.python.org/pypi/logging
__ http://pypi.python.org/pypi/setuptools
__ http://pypi.python.org/pypi/distribute


:Hints for installing on Windows: Following the links above you will
   find .msi and .exe-installers. Simply install them and continue
   with `installing managesieve`_.

:Hints for installing on GNU/Linux: Most current GNU/Linux distributions
   provide packages for the requirements. Look for packages names like
   `python-setuptools` and `python-logging`. Simply install them and
   continue with `installing managesieve`_.

:Hint for installing on other platforms: Many vendors provide Python.
   Please check your vendors software repository. Otherwise please
   download Python 2.6 (or any higer version from the 2.x series) from
   http://www.python.org/download/ and follow the installation
   instructions there.

   After installing Python, install `setuptools`__. You may want to
   read `More Hints on Installing setuptools`_ first.

__ http://pypi.python.org/pypi/setuptools


Installing managesieve
---------------------------------

When you are reading this you most probably already downloaded and
unpacked `managesieve`. Thus installing is as easy as running::

   python ./setup.py install

Otherwise you may install directly using setuptools/easy_install. If
your system has network access installing `managesieve` is a
breeze::

     easy_install managesieve

Without network access download `managesieve` from
http://python-managesieve.origo.ethz.ch/download and run::

     easy_install managesieve-*.tar.gz


More Hints on Installing setuptools
------------------------------------

`managesieve` uses setuptools for installation. Thus you need either

  * network access, so the install script will automatically download
    and install setuptools if they are not already installed

or

  * the correct version of setuptools preinstalled using the
    `EasyInstall installation instructions`__. Those instructions also
    have tips for dealing with firewalls as well as how to manually
    download and install setuptools.

__ http://peak.telecommunity.com/DevCenter/EasyInstall#installation-instructions


Custom Installation Locations
------------------------------

If you want to install the `managesieve` Python module and the
`sieveshell` script at a custom location, you can use commands like
this::

   # install to /usr/local/lib/ and /usr/local/bin
   python ./setup.py install --prefix /usr/local

   # install to your Home directory (~/bin and ~/lib/python)
   python ./setup.py install --home ~


Please mind: This effects also the installation of `logging` (and
setuptools) if they are not already installed.

For more information please refer to the `Custom Installation
Locations Instructions`__ before installing ``managesieve``.

__ http://peak.telecommunity.com/DevCenter/EasyInstall#custom-installation-locations>


Not yet implemented
~~~~~~~~~~~~~~~~~~~~~~~~

- sieve-names are only quoted dump (put into quotes, but no escapes yet).


Copyright/License
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Copyright (C) 2003-2011 by Hartmut Goebel <h.goebel@crazy-compilers.com>

License: Python Software Foundation License
         http://www.opensource.org/licenses/PythonSoftFoundation.html

License for 'sieveshell' and test suite: GPL
	http://www.opensource.org/licenses/gpl-license.php

Credits
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Based on Sieve.py from Ulrich Eck <ueck@net-labs.de> which is part of
of 'ImapClient' (see http://www.zope.org/Members/jack-e/ImapClient), a
Zope product.

Some ideas taken from imaplib written by Piers Lauder
<piers@cs.su.oz.au> et al.

Thanks to Tomas 'Skitta' Lindroos, Lorenzo Boccaccia, Alain Spineux,
darkness and Gregory Boyce for sending patches.
