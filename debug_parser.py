# -*- coding: utf-8 -*-

import json
from enum import Enum, auto
from exceptions import ParseError
import time


class DebugParser:
    class States(Enum):
        IAMSTUPID = auto()
        FINISH = auto()
        ELEM_START = auto()
        FIRST_ARRAY_ELEM_START = auto()
        OBJ_KEY_START_OR_OBJ_END = auto()
        OBJ_KEY_START = auto()
        OBJ_KEY_CONTINUE = auto()
        OBJ_KEY = auto()
        OBJ_KEY_ESC = auto()
        OBJ_KEY_VALUE_COLON = auto()
        NEG_LITERAL = auto()
        INT_LITERAL = auto()
        INT_ZERO_LITERAL = auto()
        FLOAT_LITERAL = auto()
        EXP_SEPARATOR = auto()
        EXP_SIGN = auto()
        EXP_LITERAL = auto()
        STR_LITERAL = auto()
        STR_LITERAL_ESC = auto()
        HEX_ESC = auto()
        HEX_DIGIT1 = auto()
        HEX_DIGIT2 = auto()
        HEX_DIGIT3 = auto()
        ARR_ELEM_CONTINUE = auto()
        TRUE_LITERAL_T = auto()
        TRUE_LITERAL_R = auto()
        TRUE_LITERAL_U = auto()
        FALSE_LITERAL_F = auto()
        FALSE_LITERAL_A = auto()
        FALSE_LITERAL_L = auto()
        FALSE_LITERAL_S = auto()
        NULL_LITERAL_N = auto()
        NULL_LITERAL_U = auto()
        NULL_LITERAL_L = auto()
        NAN_LITERAL_N = auto()
        NAN_LITERAL_A = auto()
        POSITIVE_INFINITY_I = auto()
        POSITIVE_INFINITY_N = auto()
        POSITIVE_INFINITY_F = auto()
        POSITIVE_INFINITY_I2 = auto()
        POSITIVE_INFINITY_N2 = auto()
        POSITIVE_INFINITY_I3 = auto()
        POSITIVE_INFINITY_T = auto()
        NEGATIVE_INFINITY_I = auto()
        NEGATIVE_INFINITY_N = auto()
        NEGATIVE_INFINITY_F = auto()
        NEGATIVE_INFINITY_I2 = auto()
        NEGATIVE_INFINITY_N2 = auto()
        NEGATIVE_INFINITY_I3 = auto()
        NEGATIVE_INFINITY_T = auto()

    def __init__(self):
        self.state = self.States.ELEM_START
        self.index = 0
        self.stack = [self.States.FINISH]
        self.token = ''

    def parse(self, gen):
        print("parser: data loop start")
        for data in gen:
            print("parser: data load start")
            start = time.time()
            self._load(data)
            elapsed_time = time.time() - start
            print("parser: data load end in {:.8f}".format(elapsed_time))
            print("parser: parse loop start")
            start = time.time()
            for event in self._parse_chunk():
                elapsed_time = time.time() - start
                print("parser: event iter in {}".format(elapsed_time))
                yield event
            elapsed_time = time.time() - start
            print("parser: parse loop end in {}".format(elapsed_time))
        print("parser: data loop end")

        print("parser: end of data loop start")
        for event in self._parse_chunk(end_of_data=True):
            yield event
        print("parser: end of data loop end")

    def _load(self, s):
        if type(s) is bytes:
            self.data = s.decode("utf-8")
        else:
            self.data = s
        self.local_index = 0

    def _parse_chunk(self, end_of_data=False):
        if end_of_data:
            raise StopIteration()
        # if end_of_data and self.local_index == len(self.data):
        #     if self.state == self.State.FINISH:
        #         pass
        #     elif self.state in [self.State.INT_LITERAL, self.State.INT_ZERO_LITERAL]:
        #         self.state = self.stack.pop()
        #         yield ("value_end", int(self.token))
        #         self.token = ''
        #         if self.state != self.State.FINISH:
        #             self._raise_parse_error("<end of data>")
        #     elif self.state in [self.State.FLOAT_LITERAL, self.State.EXP_LITERAL]:
        #         self.state = self.stack.pop()
        #         yield ("value_end", float(self.token))
        #         self.token = ''
        #         if self.state != self.State.FINISH:
        #             self._raise_parse_error("<end of data>")
        #     else:
        #         self._raise_parse_error("<end of data>")

        loop_start = time.time()

        iter_times = []

        for ch in self.data[self.local_index:]:
            start = time.time()
            self.local_index += 1
            self.index += 1

            if (self.state == self.States.STR_LITERAL or self.state == self.States.OBJ_KEY) and ch not in ['"', '\\']:
                if ord(ch) > 31:
                    self.token += ch
                else:
                    self.raise_parse_error(ch)

            elif self.state == self.States.STR_LITERAL_ESC:
                if ch in ['"', '\\', '/', 'b', 'f', 'n', 'r', 't', 'u']:
                    self.token += ch
                    self.state = self.States.STR_LITERAL
                elif ch == 'u':
                    self.stack.append(self.States.STR_LITERAL)
                    self.token += ch
                    self.state = self.States.HEX_ESC
                else:
                    self.raise_parse_error(ch)

            elif self.state == self.States.OBJ_KEY_ESC:
                if ch in ['"', '\\', '/', 'b', 'f', 'n', 'r', 't']:
                    self.token += ch
                    self.state = self.States.OBJ_KEY
                elif ch == 'u':
                    self.stack.append(self.States.OBJ_KEY)
                    self.token += ch
                    self.state = self.States.HEX_ESC
                else:
                    self.raise_parse_error(ch)

            elif ch == '\\':
                if self.state == self.States.STR_LITERAL:
                    self.token += ch
                    self.state = self.States.STR_LITERAL_ESC
                elif self.state == self.States.OBJ_KEY:
                    self.token += ch
                    self.state = self.States.OBJ_KEY_ESC
                else:
                    self.raise_parse_error(ch)

            elif ch == 'b':
                if self.state == self.States.HEX_ESC:
                    self.token += ch
                    self.state = self.States.HEX_DIGIT1
                elif self.state == self.States.HEX_DIGIT1:
                    self.token += ch
                    self.state = self.States.HEX_DIGIT2
                elif self.state == self.States.HEX_DIGIT2:
                    self.token += ch
                    self.state = self.States.HEX_DIGIT3
                elif self.state == self.States.HEX_DIGIT3:
                    self.token += ch
                    self.state = self.stack.pop()
                else:
                    self.raise_parse_error(ch)

            elif ch.isspace():
                pass

            elif ch == "[":
                if self.state in [self.States.ELEM_START, self.States.FIRST_ARRAY_ELEM_START]:
                    self.stack.append(self.States.ARR_ELEM_CONTINUE)
                    self.state = self.States.FIRST_ARRAY_ELEM_START
                    # yield ("array_start", None)
                else:
                    self.raise_parse_error(ch)

            elif ch == "]":
                if self.state in [self.States.INT_LITERAL, self.States.INT_ZERO_LITERAL]:
                    self.state = self.stack.pop()
                    # yield ("value_end", int(self.token))
                    self.token = ''
                elif self.state in [self.States.FLOAT_LITERAL, self.States.EXP_LITERAL]:
                    self.state = self.stack.pop()
                    # yield ("value_end", float(self.token))
                    self.token = ''

                if self.state == self.States.ARR_ELEM_CONTINUE:
                    self.state = self.stack.pop()
                    # yield ("array_end", None)
                elif self.state == self.States.FIRST_ARRAY_ELEM_START:
                    self.state = self.stack.pop()
                    self.state = self.stack.pop()
                    # yield ("array_end", None)
                else:
                    self.raise_parse_error(ch)

            elif ch == "{":
                if self.state in [self.States.ELEM_START, self.States.FIRST_ARRAY_ELEM_START]:
                    self.state = self.States.OBJ_KEY_START_OR_OBJ_END
                    # yield ("object_start", None)
                else:
                    self.raise_parse_error(ch)

            elif ch == "}":
                if self.state in [self.States.INT_LITERAL, self.States.INT_ZERO_LITERAL]:
                    self.state = self.stack.pop()
                    # yield ("value_end", int(self.token))
                    self.token = ''
                elif self.state in [self.States.FLOAT_LITERAL, self.States.EXP_LITERAL]:
                    self.state = self.stack.pop()
                    # yield ("value_end", float(self.token))
                    self.token = ''

                if self.state in [self.States.OBJ_KEY_START_OR_OBJ_END, self.States.OBJ_KEY_CONTINUE]:
                    # yield ("object_end", None)
                    self.state = self.stack.pop()
                else:
                    self.raise_parse_error(ch)

            elif ch == ":":
                if self.state == self.States.OBJ_KEY_VALUE_COLON:
                    self.stack.append(self.States.OBJ_KEY_CONTINUE)
                    self.state = self.States.ELEM_START
                else:
                    self.raise_parse_error(ch)

            elif ch == '"':
                if self.state in [self.States.ELEM_START, self.States.FIRST_ARRAY_ELEM_START]:
                    # yield ("value_start", None)
                    self.state = self.States.STR_LITERAL
                elif self.state in [self.States.OBJ_KEY_START, self.States.OBJ_KEY_START_OR_OBJ_END]:
                    # yield ("object_key_start", None)
                    self.state = self.States.OBJ_KEY
                elif self.state == self.States.OBJ_KEY:
                    try:
                        token = json.loads('"' + self.token + '"')
                    except json.decoder.JSONDecodeError:
                        self.raise_parse_error(ch)
                    # yield ("object_key_end", token)
                    self.token = ''
                    self.state = self.States.OBJ_KEY_VALUE_COLON
                elif self.state == self.States.STR_LITERAL:
                    try:
                        token = json.loads('"' + self.token + '"')
                    except json.decoder.JSONDecodeError:
                        self.raise_parse_error(ch)
                    # yield ("value_end", token)
                    self.token = ''
                    self.state = self.stack.pop()
                else:
                    self.raise_parse_error(ch)

            elif ch == ',':
                if self.state in [self.States.INT_LITERAL, self.States.INT_ZERO_LITERAL]:
                    self.state = self.stack.pop()
                    # yield ("value_end", int(self.token))
                    self.token = ''
                elif self.state in [self.States.FLOAT_LITERAL, self.States.EXP_LITERAL]:
                    self.state = self.stack.pop()
                    # yield ("value_end", float(self.token))
                    self.token = ''

                if self.state == self.States.OBJ_KEY_CONTINUE:
                    self.state = self.States.OBJ_KEY_START
                elif self.state == self.States.ARR_ELEM_CONTINUE:
                    self.stack.append(self.States.ARR_ELEM_CONTINUE)
                    self.state = self.States.ELEM_START
                else:
                    self.raise_parse_error(ch)

            elif ch == "-":
                if self.state in [self.States.ELEM_START, self.States.FIRST_ARRAY_ELEM_START]:
                    # yield ("value_start", None)
                    self.token += ch
                    self.state = self.States.NEG_LITERAL
                elif self.state == self.States.EXP_SEPARATOR:
                    self.token += ch
                    self.state = self.States.EXP_SIGN
                else:
                    self.raise_parse_error(ch)

            elif ch == "+":
                if self.state == self.States.EXP_SEPARATOR:
                    self.token += ch
                    self.state = self.States.EXP_SIGN
                else:
                    self.raise_parse_error(ch)

            elif ch.isdigit():
                if self.state in [self.States.ELEM_START, self.States.FIRST_ARRAY_ELEM_START]:
                    # yield ("value_start", None)
                    self.token += ch
                    if ch == "0":
                        self.state = self.States.INT_ZERO_LITERAL
                    else:
                        self.state = self.States.INT_LITERAL
                elif self.state == self.States.NEG_LITERAL:
                    self.token += ch
                    self.state = self.States.INT_LITERAL
                elif self.state == self.States.EXP_SEPARATOR:
                    self.token += ch
                    self.state = self.States.EXP_LITERAL
                elif self.state == self.States.EXP_SIGN:
                    self.token += ch
                    self.state = self.States.EXP_LITERAL
                elif self.state in [self.States.INT_LITERAL, self.States.FLOAT_LITERAL, self.States.EXP_LITERAL]:
                    self.token += ch
                elif self.state == self.States.HEX_ESC:
                    self.token += ch
                    self.state = self.States.HEX_DIGIT1
                elif self.state == self.States.HEX_DIGIT1:
                    self.token += ch
                    self.state = self.States.HEX_DIGIT2
                elif self.state == self.States.HEX_DIGIT2:
                    self.token += ch
                    self.state = self.States.HEX_DIGIT3
                elif self.state == self.States.HEX_DIGIT3:
                    self.token += ch
                    self.state = self.stack.pop()
                else:
                    self.raise_parse_error(ch)

            elif ch == ".":
                if self.state in [self.States.INT_LITERAL, self.States.INT_ZERO_LITERAL]:
                    self.token += ch
                    self.state = self.States.FLOAT_LITERAL
                else:
                    self.raise_parse_error(ch)

            elif ch in ["e", "E"]:
                if self.state in [self.States.INT_LITERAL, self.States.FLOAT_LITERAL]:
                    self.token += ch
                    self.state = self.States.EXP_SEPARATOR
                elif ch == 'e' and self.state == self.States.TRUE_LITERAL_U:
                    # yield ("value_end", True)
                    self.state = self.stack.pop()
                elif ch == 'e' and self.state == self.States.FALSE_LITERAL_S:
                    # yield ("value_end", False)
                    self.state = self.stack.pop()
                elif self.state == self.States.HEX_ESC:
                    self.token += ch
                    self.state = self.States.HEX_DIGIT1
                elif self.state == self.States.HEX_DIGIT1:
                    self.token += ch
                    self.state = self.States.HEX_DIGIT2
                elif self.state == self.States.HEX_DIGIT2:
                    self.token += ch
                    self.state = self.States.HEX_DIGIT3
                elif self.state == self.States.HEX_DIGIT3:
                    self.token += ch
                    self.state = self.stack.pop()
                else:
                    self.raise_parse_error(ch)

            elif ch == 't':
                if self.state in [self.States.ELEM_START, self.States.FIRST_ARRAY_ELEM_START]:
                    # yield ("value_start", None)
                    self.state = self.States.TRUE_LITERAL_T
                elif self.state == self.States.POSITIVE_INFINITY_I3:
                    self.state = self.States.POSITIVE_INFINITY_T
                elif self.state == self.States.NEGATIVE_INFINITY_I3:
                    self.state = self.States.NEGATIVE_INFINITY_T
                else:
                    self.raise_parse_error(ch)

            elif ch == 'r':
                if self.state == self.States.TRUE_LITERAL_T:
                    self.state = self.States.TRUE_LITERAL_R
                else:
                    self.raise_parse_error(ch)

            elif ch == 'u':
                if self.state == self.States.TRUE_LITERAL_R:
                    self.state = self.States.TRUE_LITERAL_U
                elif self.state == self.States.NULL_LITERAL_N:
                    self.state = self.States.NULL_LITERAL_U
                else:
                    self.raise_parse_error(ch)

            elif ch == 'a':
                if self.state == self.States.FALSE_LITERAL_F:
                    self.state = self.States.FALSE_LITERAL_A
                elif self.state == self.States.NAN_LITERAL_N:
                    self.state = self.States.NAN_LITERAL_A
                elif self.state == self.States.HEX_ESC:
                    self.token += ch
                    self.state = self.States.HEX_DIGIT1
                elif self.state == self.States.HEX_DIGIT1:
                    self.token += ch
                    self.state = self.States.HEX_DIGIT2
                elif self.state == self.States.HEX_DIGIT2:
                    self.token += ch
                    self.state = self.States.HEX_DIGIT3
                elif self.state == self.States.HEX_DIGIT3:
                    self.token += ch
                    self.state = self.stack.pop()
                else:
                    self.raise_parse_error(ch)

            elif ch == 'f':
                if self.state in [self.States.ELEM_START, self.States.FIRST_ARRAY_ELEM_START]:
                    # yield ("value_start", None)
                    self.state = self.States.FALSE_LITERAL_F
                elif self.state == self.States.POSITIVE_INFINITY_N:
                    self.state = self.States.POSITIVE_INFINITY_F
                elif self.state == self.States.NEGATIVE_INFINITY_N:
                    self.state = self.States.NEGATIVE_INFINITY_F
                elif self.state == self.States.HEX_ESC:
                    self.token += ch
                    self.state = self.States.HEX_DIGIT1
                elif self.state == self.States.HEX_DIGIT1:
                    self.token += ch
                    self.state = self.States.HEX_DIGIT2
                elif self.state == self.States.HEX_DIGIT2:
                    self.token += ch
                    self.state = self.States.HEX_DIGIT3
                elif self.state == self.States.HEX_DIGIT3:
                    self.token += ch
                    self.state = self.stack.pop()
                else:
                    self.raise_parse_error(ch)

            elif ch == 'l':
                if self.state == self.States.FALSE_LITERAL_A:
                    self.state = self.States.FALSE_LITERAL_L
                elif self.state == self.States.NULL_LITERAL_U:
                    self.state = self.States.NULL_LITERAL_L
                elif self.state == self.States.NULL_LITERAL_L:
                    # yield ("value_end", None)
                    self.state = self.stack.pop()
                else:
                    self.raise_parse_error(ch)

            elif ch == 's':
                if self.state == self.States.FALSE_LITERAL_L:
                    self.state = self.States.FALSE_LITERAL_S
                else:
                    self.raise_parse_error(ch)

            elif ch == 'n':
                if self.state in [self.States.ELEM_START, self.States.FIRST_ARRAY_ELEM_START]:
                    # yield ("value_start", None)
                    self.state = self.States.NULL_LITERAL_N
                elif self.state == self.States.POSITIVE_INFINITY_I:
                    self.state = self.States.POSITIVE_INFINITY_N
                elif self.state == self.States.POSITIVE_INFINITY_I2:
                    self.state = self.States.POSITIVE_INFINITY_N2
                elif self.state == self.States.NEGATIVE_INFINITY_I:
                    self.state = self.States.NEGATIVE_INFINITY_N
                elif self.state == self.States.NEGATIVE_INFINITY_I2:
                    self.state = self.States.NEGATIVE_INFINITY_N2
                else:
                    self.raise_parse_error(ch)

            elif ch == 'N':
                if self.state == self.States.ELEM_START:
                    # yield ("value_start", None)
                    self.state = self.States.NAN_LITERAL_N
                elif self.state == self.States.NAN_LITERAL_A:
                    # yield ("value_end", float('nan'))
                    self.state = self.stack.pop()
                else:
                    self.raise_parse_error(ch)

            elif ch == 'I':
                if self.state in [self.States.ELEM_START, self.States.FIRST_ARRAY_ELEM_START]:
                    # yield ("value_start", None)
                    self.state = self.States.POSITIVE_INFINITY_I
                elif self.state == self.States.NEG_LITERAL:
                    self.state = self.States.NEGATIVE_INFINITY_I
                else:
                    self.raise_parse_error(ch)

            elif ch == 'i':
                if self.state == self.States.POSITIVE_INFINITY_F:
                    self.state = self.States.POSITIVE_INFINITY_I2
                elif self.state == self.States.POSITIVE_INFINITY_N2:
                    self.state = self.States.POSITIVE_INFINITY_I3
                elif self.state == self.States.NEGATIVE_INFINITY_F:
                    self.state = self.States.NEGATIVE_INFINITY_I2
                elif self.state == self.States.NEGATIVE_INFINITY_N2:
                    self.state = self.States.NEGATIVE_INFINITY_I3
                else:
                    self.raise_parse_error(ch)

            elif ch == 'y':
                if self.state == self.States.POSITIVE_INFINITY_T:
                    # yield ('value_end', float('inf'))
                    self.state = self.stack.pop()
                if self.state == self.States.NEGATIVE_INFINITY_T:
                    # yield ('value_end', float('-inf'))
                    self.state = self.stack.pop()
                else:
                    self.raise_parse_error(ch)

            elif ch in ['c', 'd', 'A', 'B', 'C', 'D', 'F']:
                if self.state == self.States.HEX_ESC:
                    self.token += ch
                    self.state = self.States.HEX_DIGIT1
                elif self.state == self.States.HEX_DIGIT1:
                    self.token += ch
                    self.state = self.States.HEX_DIGIT2
                elif self.state == self.States.HEX_DIGIT2:
                    self.token += ch
                    self.state = self.States.HEX_DIGIT3
                elif self.state == self.States.HEX_DIGIT3:
                    self.token += ch
                    self.state = self.stack.pop()
                else:
                    self.raise_parse_error(ch)
            #
            # else:
            #     self._raise_parse_error(ch)
            # elapsed_time = time.time() - start
            # print("{} {:.8f}".format(ch, elapsed_time))
            # iter_times.append(elapsed_time)

        # for it in iter_times:
            # print("{:.8f}".format(it))
        loop_elapsed_time = time.time() - loop_start
        print("loop_in_parser={}".format(loop_elapsed_time))
        print("iters={}".format(self.index))
        print("iter_time={}".format(loop_elapsed_time / self.index))
        # print(len(iter_times))
        # print("loop_in_parser sum={}".format(sum(iter_times)))
        yield ("value_end", "!!! ")
        # print("loop_in_parser_post_yield={}".format(sum(iter_times)))

    def raise_parse_error(self, ch):
        raise ParseError("Parse error: unexpected char '%s' in state %s (local index %d, global index %d)" % (
            ch,
            self.state.name,
            self.local_index,
            self.index
          ))
