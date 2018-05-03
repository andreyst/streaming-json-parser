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
        fp = open(fixture_filename, mode='r')
        try:
            data_gen = iter(lambda: fp.read(4), '')
            decoder = Decoder(data_gen)
            data = decoder.decode()
        finally:
            fp.close()

        return data

    # Fixtures taken from https://github.com/nst/JSONTestSuite/
    def testPassFixtures(self):
        for fixture_filename in glob.glob(self.cur_dir + "/json-checker/y_*"):
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

    # Fixtures taken from https://github.com/nst/JSONTestSuite/
    def testFailFixtures(self):
        for fixture_filename in glob.glob(self.cur_dir + "/json-checker/n_*"):
            with self.subTest(fixture_filename=os.path.basename(fixture_filename)):
                raised = False
                try:
                    TestDecoder._decode_fixture(fixture_filename)
                except ParseError:
                    raised = True
                if not raised:
                    self.fail(msg="Fixture not failed: " + fixture_filename)

    # Fixtures taken from https://github.com/nst/JSONTestSuite/
    # Implementation-specific tests should just run without crashing
    def testImplementationFixtures(self):
        for fixture_filename in glob.glob(self.cur_dir + "/json-test-suite/i_*"):
            with self.subTest(fixture_filename=os.path.basename(fixture_filename)):
                try:
                    TestDecoder._decode_fixture(fixture_filename)
                except (UnicodeDecodeError, ParseError):
                    # These test may and should raise this exceptions
                    pass

    # Fixtures taken from https://github.com/nst/JSONTestSuite/
    # Transform tests should just run without crashing
    def testTransformFixtures(self):
        for fixture_filename in glob.glob(self.cur_dir + "/json-test-suite/t_*"):
            with self.subTest(fixture_filename=os.path.basename(fixture_filename)):
                try:
                    TestDecoder._decode_fixture(fixture_filename)
                except UnicodeDecodeError:
                    # These test may and should raise this exception
                    pass


if __name__ == '__main__':
    unittest.main()
