#!/usr/bin/env python
"""
Deveploment utility for testing patterns.
"""

import re

Oknobye = re.compile(r'(?P<type>(OK|NO|BYE))'
                     r'( \((?P<code>.*)\))?'
                     r'( (?P<data>.*))?')

def test_re(cre, string):
    mo = cre.match(string)
    if mo:
        print mo.group('type'), mo.group('code'), mo.group('data')

test_re(Oknobye, 'OK')
test_re(Oknobye, 'OK (OKAY/ALL)')
test_re(Oknobye, 'OK "Hi di How!"')
test_re(Oknobye, 'OK (OKAY/ALL) "Hi di How!"')
