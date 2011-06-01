#!/usr/bin/env python

"""Setup script for the managesieve"""

import ez_setup
ez_setup.use_setuptools()
from setuptools import setup

description = "ManageSieve client library for remotely managing Sieve scripts"

from distutils.command.bdist_rpm import bdist_rpm

# patch distutils if it can't cope with the "classifiers" or
# "download_url" keywords
import sys
if sys.version_info < (2,2,3):
    from distutils.dist import DistributionMetadata
    DistributionMetadata.classifiers = None
    DistributionMetadata.download_url = None

install_requires = []
if sys.version_info < (2,3):
    install_requires.append('logging')


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


setup (name = "managesieve",
       version = "0.4.2",
       description = description,
       long_description = open('README.txt').read().strip(),
       author = "Hartmut Goebel",
       author_email = "h.goebel@crazy-compilers.com",
       #maintainer = "Hartmut Goebel",
       #maintainer_email = "h.goebel@crazy-compilers.com",
       url = "http://python-managesieve.origo.ethz.ch/",
       download_url = "http://python-managesieve.origo.ethz.ch/download",
       license = 'Python',
       platforms = ['POSIX'],
       keywords = ['sieve', 'managesieve', 'sieveshell', 'RFC 5804'],
       py_modules = ['managesieve'],
       scripts = ['sieveshell'],
       install_requires = install_requires,
       cmdclass = {'bdist_rpm': MyBDist_RPM},
       classifiers = [
          'Development Status :: 5 - Production/Stable',
          'Environment :: Console',
          'Intended Audience :: End Users/Desktop',
          'Intended Audience :: Developers',
          #'Intended Audience :: System Administrators',
          'License :: OSI Approved :: Python Software Foundation License',
          'License :: OSI Approved :: GNU General Public License (GPL)',
          'Natural Language :: English',
          #'Operating System :: MacOS :: MacOS X',
          #'Operating System :: Microsoft :: Windows',
          #'Operating System :: POSIX',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Topic :: Communications :: Email',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Topic :: Utilities'
          ],
     )
