#!/usr/bin/env python

"""Setup script for the managesieve"""

from distutils.core import setup

description = "MANAGESIEVE client library for remotely managing Sieve scripts"
long_description = """
A MANGAGESIEVE client library for remotely managing Sieve scripts,
including an interactive 'sieveshell'.

This module allows accessing a Sieve-Server for managing Sieve scripts
there. For more information about the MANAGESIEVE protocol see draft
http://www.ietf.org/internet-drafts/draft-martin-managesieve-04.txt .


What is MANAGESIEVE?
--------------------

Sieve scripts allow users to filter incoming email. Message stores are
commonly sealed servers so users cannot log into them, yet users must
be able to update their scripts on them. This module implements a
protocol "managesieve" for securely managing Sieve scripts on a remote
server. This protocol allows a user to have multiple scripts, and also
alerts a user to syntactically flawed scripts.

This an interim measure as it is hoped that eventually Sieve scripts
will be stored on ACAP.
""" # " emacs happy

from distutils.command.bdist_rpm import bdist_rpm

class MyBDist_RPM(bdist_rpm):
    """Wrapper for 'bdist_rpm' handling 'python2'"""
    def finalize_options(self):
        if self.fix_python:
            import sys
            if sys.executable.endswith('/python2'):
                # this should be more sophisticated, but this
                # works for our needs here
                self.requires = self.requires.replace('python ', 'python2 ')
                self.build_requires = self.build_requires.replace('python ',
                                                                  'python2 ')
                self.release = (self.release or "1") + 'python2'
        bdist_rpm.finalize_options(self)


setup (name = "python-managesieve",
       version = "0.2",
       description = description,
       long_description = long_description,
       author = "Hartmut Goebel",
       author_email = "h.goebel@crazy-compilers.com",
       #maintainer = "Hartmut Goebel",
       #maintainer_email = "h.goebel@crazy-compilers.com",
       url = "http://www.crazy-compilers.com/py-lib/#managesieve",
       license = 'Python',
       platforms = ['POSIX'],
       keywords = ['sieve', 'managesieve', 'sieveshell', 'command-line'],
       py_modules = ['managesieve'],
       cmdclass = {'bdist_rpm': MyBDist_RPM},
      )
