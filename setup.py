# -*- coding: utf-8 -*-
"""
managesieve-cli
---------------

A command-line client for interacting with ManageSieve servers, fork of
http://pypi.python.org/pypi/managesieve

"""
from setuptools import setup

description = "ManageSieve client library for remotely managing Sieve scripts"


setup(
    name="managesieve",
    version="0.4.4-dev",
    description=("A command-line client for interacting with "
                 "ManageSieve servers."),
    long_description=__doc__,
    author="Daniel Kertesz",
    author_email="daniel@spatof.org",
    url="https://github.com/piger/managesieve-cli",
    license='GPLv3',
    platforms=['POSIX'],
    keywords=['sieve', 'managesieve', 'sieveshell', 'RFC 5804'],
    packages=['managesieve'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Python Software Foundation License',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        #'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        #'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Communications :: Email',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities'
    ],
    entry_points={
        "console_scripts": [
            "managesieve-cli = managesieve.cli:main",
        ],
    },
)
