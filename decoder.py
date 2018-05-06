# -*- coding: utf-8 -*-

from parser import Parser
from exceptions import ParseError
import time

class Decoder:
    def __init__(self, data_gen):
        parser = Parser()
        self.parser_gen = parser.parse(data_gen)

    def decode(self):
        evt, res = self._parse_sub_tree()
        # print("decode result: ", evt, res)

        try:
            evt, res = next(self.parser_gen)
            # print("event after decoder loop: ", evt, res)
            raise ParseError("Extra data after close")
        except StopIteration:
            pass

        return res

    def _parse_sub_tree(self):
        obj = None

        while True:
            start = time.time()
            # print("parser_in_decoder: loop start")
            evt_name, evt_param = next(self.parser_gen)
            # print("event in decoder loop: ", evt_name, evt_param)
            # print("parser_in_decoder: loop end")
            elapsed_time = time.time() - start
            # print("parser_in_decoder={}".format(elapsed_time))
            if evt_name == "object_start":
                obj = {}
            elif evt_name == "object_key_end":
                key = evt_param
                _, value = self._parse_sub_tree()
                obj[key] = value
            elif evt_name == "object_end":
                return True, obj
            elif evt_name == "array_start":
                obj = []
                while True:
                    is_data, value = self._parse_sub_tree()
                    if is_data:
                        obj.append(value)
                    else:
                        return True, obj
            elif evt_name == "array_end":
                return False, None
            elif evt_name == "value_end":
                return True, evt_param
