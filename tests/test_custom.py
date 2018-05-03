# -*- coding: utf-8 -*-

from decoder import Decoder
from parser import ParseError
import unittest
import json
import math

class TestDecoder(unittest.TestCase):

    def testStandaloneLiterals(self):
        test_datum = [
            '"string"',
            'true',
            'false',
            'NaN',
            'null',
            'Infinity',
            '-Infinity',
            '999',
            '1.00',
            '-1.00'
            '1e5',
            '2.3e4',
            '0',
            '[0]',
            '{"a":0}',
        ]

        for test_data in test_datum:
            with self.subTest(test_data=test_data):
                decoder = Decoder(s for s in [test_data])
                d = decoder.decode()
                json_d = json.loads(test_data)
                if type(d) is not float or not math.isnan(d):
                    self.assertEqual(d, json_d)
                else:
                    self.assertTrue(math.isnan(json_d))

    def testFailures(self):
        test_datum = [
            '+Infinity'
            '1..00',
            '1.e1',
        ]

        for test_data in test_datum:
            with self.subTest(test_data=test_data):
                with self.assertRaises(ParseError):
                    decoder = Decoder(s for s in [test_data])
                    decoder.decode()


if __name__ == '__main__':
    unittest.main()
