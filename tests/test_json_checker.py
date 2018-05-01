# -*- coding: utf-8 -*-

from decoder import Decoder
from exceptions import ParseError
import deep_eq
import unittest
import glob
import os
import json


class TestDecoder(unittest.TestCase):

    cur_dir = os.path.dirname(os.path.realpath(__file__))

    @staticmethod
    def _decode_fixture(fixture_filename):
        fp = open(fixture_filename, 'r')
        try:
            data_gen = iter(lambda: fp.read(4), '')
            decoder = Decoder(data_gen)
            data = decoder.decode()
        finally:
            fp.close()

        return data

    # Fixtures taken from http://json.org/JSON_checker/test.zip
    def testPassFixtures(self):
        for fixture_filename in glob.glob(self.cur_dir + "/json-checker/pass*"):
            with self.subTest(fixture_filename=os.path.basename(fixture_filename)):
                with open(fixture_filename, 'r') as fixture_file:
                    fixture = fixture_file.read()
                reference_data = json.loads(fixture)
                try:
                    data = TestDecoder._decode_fixture(fixture_filename)
                except ParseError:
                    self.fail(msg="Fixture not passed: " + fixture_filename)

                is_eq = deep_eq.deep_eq(data, reference_data)
                if not is_eq:
                    print("")
                    print(data)
                    print(reference_data)
                self.assertTrue(is_eq, msg="Decoded data not equals reference data: " + fixture_filename)

    # Fixtures taken from http://json.org/JSON_checker/test.zip
    def testFailFixtures(self):
        for fixture_filename in glob.glob(self.cur_dir + "/json-checker/fail*"):
            with self.subTest(fixture_filename=os.path.basename(fixture_filename)):
                raised = False
                try:
                    TestDecoder._decode_fixture(fixture_filename)
                except ParseError:
                    raised = True
                if not raised:
                    self.fail(msg="Fixture not failed: " + fixture_filename)


if __name__ == '__main__':
    unittest.main()
