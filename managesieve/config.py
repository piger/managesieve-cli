# -*- coding: utf-8 -*-
"""
    managesieve.config
    ~~~~~~~~~~~~~~~~~~

    Configuration file handling.

    :copyright: (c) 2013 by Daniel Kertesz <daniel@spatof.org>
    :license: GNU Public License v3 (GPLv3)
"""
import ConfigParser


class ConfigError(Exception): pass


def parse_config_file(filename):
    config = {}
    cp = ConfigParser.SafeConfigParser()
    cp.read(filename)

    for section in cp.sections():
        if section.startswith('account'):
            name = section.split(' ', 1)[1]
            if name == "general":
                raise ConfigError("Name 'general' is reserved")
        else:
            name = section
        section_config = dict(cp.items(section))
        config[name] = section_config

    # Add a general section if missing
    if not 'general' in config:
        config['general'] = {}

    return config
