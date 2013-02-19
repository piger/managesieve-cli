#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This is a simple wrapper to launch `managesieve-cli` without even installing
it; I'm creating this because my friend jaromil doesn't like Python yet he like
to be pythoned a lot.
"""
from managesieve import cli

if __name__ == '__main__':
    cli.main()
