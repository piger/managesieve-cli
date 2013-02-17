# -*- coding: utf-8 -*-
from __future__ import with_statement
import re
import os

_cfg_line = re.compile(r'\s+=\s+')

def read_config_defaults(filename, parser):
    config = {}
    with open(filename) as fd:
        for n, line in enumerate(fd):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            try:
                name, value = _cfg_line.split(line, 1)
            except ValueError:
                raise SyntaxError("Error in config file at line %d" % n+1)
            config[name] = value
    parser.set_defaults(**config)
