# -*- coding: utf-8 -*-

from decoder import Decoder
from exceptions import ParseError
import deep_eq
import unittest
import glob
import os
import json


class TestDecoder(unittest.TestCase):

    # Adapted from python json tests
    def testRecursion(self):
        with self.assertRaises(RecursionError):
            decoder = Decoder(s for s in ['{"a":' * 100000 + '1' + '}' * 100000])
            decoder.decode()
        with self.assertRaises(RecursionError):
            decoder = Decoder(s for s in ['{"a":' * 100000 + '[1]' + '}' * 100000])
            decoder.decode()
        with self.assertRaises(RecursionError):
            decoder = Decoder(s for s in ['[' * 100000 + '1' + ']' * 100000])
            decoder.decode()

    # Adapted from python json tests
    def testOutOfRange(self):
        decoder = Decoder(s for s in ['[23456789012E666]'])
        self.assertEqual(decoder.decode(), [float('inf')])
        decoder = Decoder(s for s in ['[-23456789012E666]'])
        self.assertEqual(decoder.decode(), [float('-inf')])

    # Adapted from python json tests
    def testBadData(self):
        testDatum = [
            '',
            '[',
            '[42',
            '[42,',
            '["',
            '["spam',
            '["spam"',
            '["spam",',
            '{',
            '{"',
            '{"spam',
            '{"spam"',
            '{"spam":',
            '{"spam":42',
            '{"spam":42,',
            '"',
            '"spam',
            '[,',
            '{"spam":[}',
            '[42:',
            '[42 "spam"',
            '[42,]',
            '{"spam":[42}',
            '["]',
            '["spam":',
            '["spam",]',
            '{:',
            '{,',
            '{42',
            '[{]',
            '{"spam",',
            '{"spam"}',
            '[{"spam"]',
            '{"spam":}',
            '[{"spam":]',
            '{"spam":42 "ham"',
            '[{"spam":42]',
            '{"spam":42,}',
            '[]]',
            '{}}',
            '[],[]',
            '{},{}',
            '42,"spam"',
            '"spam",42',
            '!',
            ' !',
            '\n!',
            '\n  \n\n     !',
        ]

        for testData in testDatum:
            with self.subTest(testData=testData):
                with self.assertRaises(ParseError):
                    decoder = Decoder(s for s in [testData])
                    decoder.decode()


if __name__ == '__main__':
    unittest.main()
