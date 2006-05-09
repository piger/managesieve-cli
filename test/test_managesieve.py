#!/usr/bin/env python
"""Unit test for managesieve.py

(C) Copyright 2003 by Hartmut Goebel <h.goebel@crazy-compilers.com>
"""

__author__ = "Hartmut Goebel <h.goebel@crazy-compilers.com>"
__version__ = "0.1"
__date__ = "2003-05-17"
__copyright__ = "(c) Copyright 2003 by Hartmut Goebel"
__license__ = "GPL"

import unittest
import managesieve

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

try:
    True
except NameError:
    True = 1==1; False is not True

def make_string(string):
    return '{%d+}%s%s' % ( len(string), CRLF, string)

def __makeResponses(responseTuples):
    resp = {}
    for typ, entries in responseTuples.items():
        l = resp[typ] = []
        for code, text in entries:
            # this in ineffizient, but simple code which is more
            # important for testing
            if code and text:
                l.append(('%s (%s) "%s"' % (typ, code, text) +CRLF,
                          '%s (%s) %s'   % (typ, code, make_string(text))+CRLF))
            elif text:
                l.append(('%s "%s"' % (typ, text) + CRLF,
                          '%s %s'   % (typ, make_string(text)) + CRLF))
            elif code:
                l.append(('%s (%s)' % (typ, code) + CRLF,))
            else:
                l.append((typ + CRLF,))
    return resp

CRLF = '\r\n'
OK = 'OK' ; NO = 'NO' ; BYE = 'BYE' # just for ease typing :-)

SieveNames = 'sieve-name1 another_sieve_name'.split()
Scripts = [
    ( 'keep ;') ,
    ( 'if header :contains "Subject" "Test ignore" {'
      '    reject ;'
      '}'),
    ]

ListScripts = ['"%s"' % s for s in SieveNames] + \
              [make_string(s) for s in SieveNames]
Script_List = [ (s, False) for s in  SieveNames ] * 2
ListScripts[2] = ListScripts[2] + " ACTIVE" # set one active
Script_List[2] = (Script_List[2][0], True)  # set one active
ListScripts = CRLF.join(ListScripts)
print ListScripts
print Script_List

RESP_OKAY       = 'Okay.'
RESP_CODE_OKAY = 'RESP-OKAY/ALL'

RESP_FAIL      = 'Failed.'
RESP_CODE_FAIL = 'RESP-FAIL/ALL'

RESP_TIMEOUT       = 'Connection timed out.'
RESP_CODE_TIMEOUT  = 'RESP-BYE/TIMEOUT'

ResponseTuples = {
    OK:  [ (None,           None),
           (None,           RESP_OKAY),
           (RESP_CODE_OKAY, None),
           (RESP_CODE_OKAY, RESP_OKAY),
           ],
    NO:  [ (None,           None),
           (None,           RESP_FAIL),
           (RESP_CODE_FAIL, None),
           (RESP_CODE_FAIL, RESP_FAIL),
           ],
    BYE: [ (None,              None),
           (None,              RESP_TIMEOUT),
           (RESP_CODE_TIMEOUT, None),
           (RESP_CODE_TIMEOUT, RESP_TIMEOUT),
           ]
    }

Responses = __makeResponses(ResponseTuples)

sieve = None

class TestSIEVE(managesieve.MANAGESIEVE):
    def __init__(self):
        self._set_response_data(Responses[OK][0][0])
        managesieve.MANAGESIEVE.__init__(self)
        #self.state = 'AUTH'
        
    def _open(self, host, port):
        # cmd_file : the buffer where the command is send to
        self.cmd_file = StringIO.StringIO()
        # resp_file: the buffer where the response is read from
        # this will be set up in __set_testdata()
        #self.file = self.resp_file = None

    def _close(self):
        pass

    def _send(self, data):
        return self.cmd_file.write(data)

    def xx_get_response(self):
        # a wrapper arround managesieve.SIEVE._get_response()
        self.cmd_file.truncate()
        self.cmd_file.seek(0)
        result = managesieve.SIEVE._get_response(self)
        self.resp_file.truncate()
        self.resp_file.seek(0)
        return result

    def _set_response_data(self, response):
        self.file = self.resp_file = StringIO.StringIO(response)

    def _get_command_data(self):
        self.cmd_file.truncate()
        self.cmd_file.seek(0)
        return self.cmd_file.getvalue()


class CommandTester(unittest.TestCase):
    def setUp(self):
        global sieve
        sieve = TestSIEVE()
        sieve.state = 'AUTH'
        pass

    def _test_simple(self, cmd_str, (resp_typ, resp_num), func, *args):
        for response in Responses[resp_typ][resp_num]:
            sieve._set_response_data(response)
            result = func(*args)
            # check if the correct command data has be send
            self.assertEqual(cmd_str, sieve._get_command_data() )
            # check if we've recieved the expected response and data
            self.assertEqual(result, resp_typ)
            self.assertEqual(sieve.response_code,
                             ResponseTuples[resp_typ][resp_num][0])
            self.assertEqual(sieve.response_text,
                             ResponseTuples[resp_typ][resp_num][1])

    def _test_with_responce_data(self, cmd_str,
                         (resp_typ, resp_num),
                         (data_str, data),
                         func, *args):
        for response in Responses[resp_typ][resp_num]:
            sieve._set_response_data(data_str + CRLF + response)
            result, dat = func(*args)
            # check if the correct command data has be send
            self.assertEqual(cmd_str, sieve._get_command_data() )

            # check if we've recieved the expected response
            self.assertEqual(result, resp_typ)
            self.assertEqual(sieve.response_code,
                             ResponseTuples[resp_typ][resp_num][0])
            self.assertEqual(sieve.response_text,
                             ResponseTuples[resp_typ][resp_num][1])
            # check if we've recieved the expected data
            if result == OK:
                self.assertEqual(dat, data)


class ManagesieveCommandsTest(CommandTester):
    def setUp(self):
        global sieve
        sieve = TestSIEVE()
        sieve.state = 'AUTH'
        sieve.debug = 0
        pass


    def testSimpleCommands1(self):
        for typ, entries in Responses.items():
            for num in range(len(entries)):
                self._test_simple(
                    ('DELETESCRIPT "%s"' + CRLF) % SieveNames[0],
                    (typ, num),
                    sieve.deletescript, SieveNames[0])

    def testSimpleCommands2(self):
        for typ, entries in Responses.items():
            for num in range(len(entries)):
                self._test_simple(
                    ('HAVESPACE "%s" 9999' + CRLF) % SieveNames[0],
                    (typ, num),
                    sieve.havespace, SieveNames[0], 9999)


    def testListScripts(self):
        for typ, entries in Responses.items():
            for num in range(len(entries)):
                self._test_with_responce_data(
                    ('LISTSCRIPTS' + CRLF),
                    (typ, num),
                    (ListScripts, Script_List),
                    sieve.listscripts)
        

    def testGetscript(self):
        for s in Scripts:
            for typ, entries in Responses.items():
                for num in range(len(entries)):
                    self._test_with_responce_data(
                        ('GETSCRIPT "%s"' + CRLF) % SieveNames[0],
                        (typ, num),
                        (make_string(s), s),
                        sieve.getscript, SieveNames[0])


    def testPutscript(self):
        for s in Scripts:
            for typ, entries in Responses.items():
                for num in range(len(entries)):
                    self._test_simple(
                        ('PUTSCRIPT "%s" %s' + CRLF) % (SieveNames[0], make_string(s)),
                        (typ, num),
                        sieve.putscript, SieveNames[0], s)


class ManagesieveAuthTest(CommandTester):
    def setUp(self):
        global sieve
        sieve = TestSIEVE()
        sieve.state = 'AUTH'

    def testLogout(self):
        for typ, entries in Responses.items():
            for num in range(len(entries)):
                self._test_simple(
                    ('LOGOUT' + CRLF),
                    (typ, num),
                    sieve.logout)
                self.assertEqual(sieve.state, 'LOGOUT')
                sieve.state = 'AUTH'


if __name__ == "__main__":
    #import pprint ; pprint.pprint(Responses) ; pprint.pprint(ResponseTuples)
    #managesieve.Debug = 5
    unittest.main()
