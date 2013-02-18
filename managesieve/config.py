# -*- coding: utf-8 -*-
import ConfigParser


def parse_config_file(filename):
    config = {}
    cp = ConfigParser.SafeConfigParser()
    cp.read(filename)

    for section in cp.sections():
        if section.startswith('account'):
            name = section.split(' ', 1)[1]
        else:
            name = section
        section_config = dict(cp.items(section))
        config[name] = section_config
    return config
