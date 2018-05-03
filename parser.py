# -*- coding: utf-8 -*-

import json
from enum import Enum, auto
from exceptions import ParseError
from functools import partial


class Parser:
    class State(Enum):
        OK = auto()
        FINISH = auto()
        OBJECT = auto()
        ARRAY = auto()
        COLON = auto()
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
        FLOAT_SEPARATOR = auto()
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

    class Mode(Enum):
        DONE = auto()
        OBJECT = auto()
        ARRAY = auto()
        KEY = auto()

    class CharClass(Enum):
        CONTROL = auto()
        SPACE = auto()
        WHITESPACE = auto()
        LEFT_CURVED_BRACKET = auto()
        RIGHT_CURVED_BRACKET = auto()
        LEFT_SQUARE_BRACKET = auto()
        RIGHT_SQUARE_BRACKET = auto()
        COLON = auto()
        COMMA = auto()
        QUOTE = auto()
        BACKSLASH = auto()
        SLASH = auto()
        PLUS = auto()
        MINUS = auto()
        POINT = auto()
        ZERO = auto()
        DIGIT = auto()
        LOW_A = auto()
        LOW_B = auto()
        LOW_C = auto()
        LOW_D = auto()
        LOW_E = auto()
        E = auto()
        LOW_F = auto()
        LOW_I = auto()
        I = auto()
        LOW_L = auto()
        LOW_N = auto()
        N = auto()
        LOW_R = auto()
        LOW_S = auto()
        LOW_T = auto()
        LOW_U = auto()
        LOW_Y = auto()
        ABCDF = auto()
        ETC = auto()
        END_OF_DATA = auto()

    class_map = {
        ' ': CharClass.SPACE,
        '{': CharClass.LEFT_CURVED_BRACKET,
        '}': CharClass.RIGHT_CURVED_BRACKET,
        '[': CharClass.LEFT_SQUARE_BRACKET,
        ']': CharClass.RIGHT_SQUARE_BRACKET,
        ':': CharClass.COLON,
        ',': CharClass.COMMA,
        '"': CharClass.QUOTE,
        '\\': CharClass.BACKSLASH,
        '/': CharClass.SLASH,
        '+': CharClass.PLUS,
        '-': CharClass.MINUS,
        '.': CharClass.POINT,
        '0': CharClass.ZERO,
        '1': CharClass.DIGIT,
        '2': CharClass.DIGIT,
        '3': CharClass.DIGIT,
        '4': CharClass.DIGIT,
        '5': CharClass.DIGIT,
        '6': CharClass.DIGIT,
        '7': CharClass.DIGIT,
        '8': CharClass.DIGIT,
        '9': CharClass.DIGIT,
        'A': CharClass.ABCDF,
        'a': CharClass.LOW_A,
        'B': CharClass.ABCDF,
        'b': CharClass.LOW_B,
        'C': CharClass.ABCDF,
        'c': CharClass.LOW_C,
        'D': CharClass.ABCDF,
        'd': CharClass.LOW_D,
        'E': CharClass.E,
        'e': CharClass.LOW_E,
        'F': CharClass.ABCDF,
        'f': CharClass.LOW_F,
        'i': CharClass.LOW_I,
        'I': CharClass.I,
        'l': CharClass.LOW_L,
        'n': CharClass.LOW_N,
        'N': CharClass.N,
        'r': CharClass.LOW_R,
        's': CharClass.LOW_S,
        't': CharClass.LOW_T,
        'u': CharClass.LOW_U,
        'y': CharClass.LOW_Y,
    }

    def get_char_class(self, ch):
        char_class = self.class_map.get(ch, None)
        if char_class is not None:
            return char_class
        if ch.isspace():
            return self.CharClass.WHITESPACE
        if ord(ch) < 32:
            return self.CharClass.CONTROL
        return self.CharClass.ETC

    def __init__(self):
        self.state = self.State.ELEM_START
        self.index = 0
        self.stack = [self.Mode.DONE]
        self.token = ''

        value_transitions = {
            self.CharClass.SPACE: self.State.ELEM_START,
            self.CharClass.WHITESPACE: self.State.ELEM_START,
            self.CharClass.LEFT_CURVED_BRACKET: self._left_curved_bracket_transition,
            self.CharClass.LEFT_SQUARE_BRACKET: self._left_square_bracket_transition,
            self.CharClass.QUOTE: self.State.STR_LITERAL,
            self.CharClass.I: self.State.POSITIVE_INFINITY_I,
            self.CharClass.N: self.State.NAN_LITERAL_N,
            self.CharClass.ZERO: self._transition_with_token_accum(self.State.INT_ZERO_LITERAL),
            self.CharClass.DIGIT: self._transition_with_token_accum(self.State.INT_LITERAL),
            self.CharClass.MINUS: self._transition_with_token_accum(self.State.NEG_LITERAL),
            self.CharClass.LOW_N: self.State.NULL_LITERAL_N,
            self.CharClass.LOW_T: self.State.TRUE_LITERAL_T,
            self.CharClass.LOW_F: self.State.FALSE_LITERAL_F,
        }

        array_transitions = dict(value_transitions)
        array_transitions[self.CharClass.RIGHT_SQUARE_BRACKET] = self._right_square_bracket_transition
        array_transitions[self.CharClass.SPACE] = self.State.ARRAY
        array_transitions[self.CharClass.WHITESPACE] = self.State.ARRAY

        self.transition_table = {
            self.State.ELEM_START: value_transitions,
            self.State.ARRAY: array_transitions,
            self.State.OBJECT: {
                self.CharClass.SPACE: self.State.OBJECT,
                self.CharClass.WHITESPACE: self.State.OBJECT,
                self.CharClass.RIGHT_CURVED_BRACKET: self._empty_right_curved_bracket_transition,
                self.CharClass.QUOTE: self.State.STR_LITERAL,
            },
            self.State.COLON: {
                self.CharClass.SPACE: self.State.COLON,
                self.CharClass.WHITESPACE: self.State.COLON,
                self.CharClass.COLON: self._colon_transition,
            },
            self.State.NEG_LITERAL: {
                self.CharClass.ZERO: self._transition_with_token_accum(self.State.INT_ZERO_LITERAL),
                self.CharClass.DIGIT: self._transition_with_token_accum(self.State.INT_LITERAL),
                self.CharClass.I: self.State.NEGATIVE_INFINITY_I,
            },
            self.State.INT_LITERAL: {
                self.CharClass.SPACE: self._numeric_literal_whitespace_transition,
                self.CharClass.WHITESPACE: self._numeric_literal_whitespace_transition,
                self.CharClass.ZERO: self._transition_with_token_accum(self.State.INT_LITERAL),
                self.CharClass.DIGIT: self._transition_with_token_accum(self.State.INT_LITERAL),
                self.CharClass.POINT: self._transition_with_token_accum(self.State.FLOAT_SEPARATOR),
                self.CharClass.COMMA: self._comma_transition,
                self.CharClass.E: self._transition_with_token_accum(self.State.EXP_SEPARATOR),
                self.CharClass.LOW_E: self._transition_with_token_accum(self.State.EXP_SEPARATOR),
                self.CharClass.RIGHT_CURVED_BRACKET: self._right_curved_bracket_transition,
                self.CharClass.RIGHT_SQUARE_BRACKET: self._right_square_bracket_transition,
                self.CharClass.END_OF_DATA: self._end_of_data_transition,
            },
            self.State.INT_ZERO_LITERAL: {
                self.CharClass.SPACE: self._numeric_literal_whitespace_transition,
                self.CharClass.WHITESPACE: self._numeric_literal_whitespace_transition,
                self.CharClass.POINT: self._transition_with_token_accum(self.State.FLOAT_SEPARATOR),
                self.CharClass.COMMA: self._comma_transition,
                self.CharClass.RIGHT_CURVED_BRACKET: self._right_curved_bracket_transition,
                self.CharClass.RIGHT_SQUARE_BRACKET: self._right_square_bracket_transition,
                self.CharClass.END_OF_DATA: self._end_of_data_transition,
            },
            self.State.FLOAT_SEPARATOR: {
                self.CharClass.ZERO: self._transition_with_token_accum(self.State.FLOAT_LITERAL),
                self.CharClass.DIGIT: self._transition_with_token_accum(self.State.FLOAT_LITERAL),
            },
            self.State.FLOAT_LITERAL: {
                self.CharClass.SPACE: self._numeric_literal_whitespace_transition,
                self.CharClass.WHITESPACE: self._numeric_literal_whitespace_transition,
                self.CharClass.ZERO: self._transition_with_token_accum(self.State.FLOAT_LITERAL),
                self.CharClass.DIGIT: self._transition_with_token_accum(self.State.FLOAT_LITERAL),
                self.CharClass.E: self._transition_with_token_accum(self.State.EXP_SEPARATOR),
                self.CharClass.LOW_E: self._transition_with_token_accum(self.State.EXP_SEPARATOR),
                self.CharClass.COMMA: self._comma_transition,
                self.CharClass.RIGHT_CURVED_BRACKET: self._right_curved_bracket_transition,
                self.CharClass.RIGHT_SQUARE_BRACKET: self._right_square_bracket_transition,
                self.CharClass.END_OF_DATA: self._end_of_data_transition,
            },
            self.State.EXP_SEPARATOR: {
                self.CharClass.ZERO: self._transition_with_token_accum(self.State.EXP_LITERAL),
                self.CharClass.DIGIT: self._transition_with_token_accum(self.State.EXP_LITERAL),
                self.CharClass.MINUS: self._transition_with_token_accum(self.State.EXP_SIGN),
                self.CharClass.PLUS: self._transition_with_token_accum(self.State.EXP_SIGN),
            },
            self.State.EXP_SIGN: {
                self.CharClass.ZERO: self._transition_with_token_accum(self.State.EXP_LITERAL),
                self.CharClass.DIGIT: self._transition_with_token_accum(self.State.EXP_LITERAL),
            },
            self.State.EXP_LITERAL: {
                self.CharClass.SPACE: self._numeric_literal_whitespace_transition,
                self.CharClass.WHITESPACE: self._numeric_literal_whitespace_transition,
                self.CharClass.ZERO: self._transition_with_token_accum(self.State.EXP_LITERAL),
                self.CharClass.DIGIT: self._transition_with_token_accum(self.State.EXP_LITERAL),
                self.CharClass.COMMA: self._comma_transition,
                self.CharClass.RIGHT_CURVED_BRACKET: self._right_curved_bracket_transition,
                self.CharClass.RIGHT_SQUARE_BRACKET: self._right_square_bracket_transition,
                self.CharClass.END_OF_DATA: self._end_of_data_transition,
            },
            self.State.STR_LITERAL: {
                self.CharClass.SPACE: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.LEFT_CURVED_BRACKET: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.RIGHT_CURVED_BRACKET: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.LEFT_SQUARE_BRACKET: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.RIGHT_SQUARE_BRACKET: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.COLON: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.COMMA: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.QUOTE: self._quote_transition,
                self.CharClass.BACKSLASH: self._transition_with_token_accum(self.State.STR_LITERAL_ESC),
                self.CharClass.SLASH: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.PLUS: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.MINUS: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.POINT: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.ZERO: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.DIGIT: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.LOW_A: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.LOW_B: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.LOW_C: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.LOW_D: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.LOW_E: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.E: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.LOW_F: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.LOW_I: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.I: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.LOW_L: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.LOW_N: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.N: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.LOW_R: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.LOW_S: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.LOW_T: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.LOW_U: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.LOW_Y: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.ABCDF: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.ETC: self._transition_with_token_accum(self.State.STR_LITERAL),
            },
            self.State.STR_LITERAL_ESC: {
                self.CharClass.QUOTE: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.SLASH: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.BACKSLASH: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.LOW_B: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.LOW_F: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.LOW_N: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.LOW_R: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.LOW_T: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.LOW_U: self._transition_with_token_accum(self.State.HEX_ESC),
            },
            self.State.HEX_ESC: {
                self.CharClass.ZERO: self._transition_with_token_accum(self.State.HEX_DIGIT1),
                self.CharClass.DIGIT: self._transition_with_token_accum(self.State.HEX_DIGIT1),
                self.CharClass.LOW_A: self._transition_with_token_accum(self.State.HEX_DIGIT1),
                self.CharClass.LOW_B: self._transition_with_token_accum(self.State.HEX_DIGIT1),
                self.CharClass.LOW_C: self._transition_with_token_accum(self.State.HEX_DIGIT1),
                self.CharClass.LOW_D: self._transition_with_token_accum(self.State.HEX_DIGIT1),
                self.CharClass.LOW_E: self._transition_with_token_accum(self.State.HEX_DIGIT1),
                self.CharClass.LOW_F: self._transition_with_token_accum(self.State.HEX_DIGIT1),
                self.CharClass.ABCDF: self._transition_with_token_accum(self.State.HEX_DIGIT1),
                self.CharClass.E: self._transition_with_token_accum(self.State.HEX_DIGIT1),
            },
            self.State.HEX_DIGIT1: {
                self.CharClass.ZERO: self._transition_with_token_accum(self.State.HEX_DIGIT2),
                self.CharClass.DIGIT: self._transition_with_token_accum(self.State.HEX_DIGIT2),
                self.CharClass.LOW_A: self._transition_with_token_accum(self.State.HEX_DIGIT2),
                self.CharClass.LOW_B: self._transition_with_token_accum(self.State.HEX_DIGIT2),
                self.CharClass.LOW_C: self._transition_with_token_accum(self.State.HEX_DIGIT2),
                self.CharClass.LOW_D: self._transition_with_token_accum(self.State.HEX_DIGIT2),
                self.CharClass.LOW_E: self._transition_with_token_accum(self.State.HEX_DIGIT2),
                self.CharClass.LOW_F: self._transition_with_token_accum(self.State.HEX_DIGIT2),
                self.CharClass.ABCDF: self._transition_with_token_accum(self.State.HEX_DIGIT2),
                self.CharClass.E: self._transition_with_token_accum(self.State.HEX_DIGIT2),
            },
            self.State.HEX_DIGIT2: {
                self.CharClass.ZERO: self._transition_with_token_accum(self.State.HEX_DIGIT3),
                self.CharClass.DIGIT: self._transition_with_token_accum(self.State.HEX_DIGIT3),
                self.CharClass.LOW_A: self._transition_with_token_accum(self.State.HEX_DIGIT3),
                self.CharClass.LOW_B: self._transition_with_token_accum(self.State.HEX_DIGIT3),
                self.CharClass.LOW_C: self._transition_with_token_accum(self.State.HEX_DIGIT3),
                self.CharClass.LOW_D: self._transition_with_token_accum(self.State.HEX_DIGIT3),
                self.CharClass.LOW_E: self._transition_with_token_accum(self.State.HEX_DIGIT3),
                self.CharClass.LOW_F: self._transition_with_token_accum(self.State.HEX_DIGIT3),
                self.CharClass.ABCDF: self._transition_with_token_accum(self.State.HEX_DIGIT3),
                self.CharClass.E: self._transition_with_token_accum(self.State.HEX_DIGIT3),
            },
            self.State.HEX_DIGIT3: {
                self.CharClass.ZERO: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.DIGIT: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.LOW_A: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.LOW_B: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.LOW_C: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.LOW_D: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.LOW_E: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.LOW_F: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.ABCDF: self._transition_with_token_accum(self.State.STR_LITERAL),
                self.CharClass.E: self._transition_with_token_accum(self.State.STR_LITERAL),
            },
            self.State.TRUE_LITERAL_T: {self.CharClass.LOW_R: self.State.TRUE_LITERAL_R},
            self.State.TRUE_LITERAL_R: {self.CharClass.LOW_U: self.State.TRUE_LITERAL_U},
            self.State.TRUE_LITERAL_U: {
                self.CharClass.LOW_E: self._transition_with_event(self.State.OK, "value_end", event_param=True)
            },
            self.State.FALSE_LITERAL_F: {self.CharClass.LOW_A: self.State.FALSE_LITERAL_A},
            self.State.FALSE_LITERAL_A: {self.CharClass.LOW_L: self.State.FALSE_LITERAL_L},
            self.State.FALSE_LITERAL_L: {self.CharClass.LOW_S: self.State.FALSE_LITERAL_S},
            self.State.FALSE_LITERAL_S: {
                self.CharClass.LOW_E: self._transition_with_event(self.State.OK, "value_end", event_param=False)
            },
            self.State.NULL_LITERAL_N: {self.CharClass.LOW_U: self.State.NULL_LITERAL_U},
            self.State.NULL_LITERAL_U: {self.CharClass.LOW_L: self.State.NULL_LITERAL_L},
            self.State.NULL_LITERAL_L: {
                self.CharClass.LOW_L: self._transition_with_event(self.State.OK, "value_end", event_param=None)
            },
            self.State.NAN_LITERAL_N: {self.CharClass.LOW_A: self.State.NAN_LITERAL_A},
            self.State.NAN_LITERAL_A: {
                self.CharClass.N: self._transition_with_event(self.State.OK, "value_end", event_param=float('nan'))
            },
            self.State.POSITIVE_INFINITY_I:  {self.CharClass.LOW_N: self.State.POSITIVE_INFINITY_N},
            self.State.POSITIVE_INFINITY_N:  {self.CharClass.LOW_F: self.State.POSITIVE_INFINITY_F},
            self.State.POSITIVE_INFINITY_F:  {self.CharClass.LOW_I: self.State.POSITIVE_INFINITY_I2},
            self.State.POSITIVE_INFINITY_I2: {self.CharClass.LOW_N: self.State.POSITIVE_INFINITY_N2},
            self.State.POSITIVE_INFINITY_N2: {self.CharClass.LOW_I: self.State.POSITIVE_INFINITY_I3},
            self.State.POSITIVE_INFINITY_I3: {self.CharClass.LOW_T: self.State.POSITIVE_INFINITY_T},
            self.State.POSITIVE_INFINITY_T:  {
                self.CharClass.LOW_Y: self._transition_with_event(self.State.OK, "value_end", event_param=float('inf'))
            },
            self.State.NEGATIVE_INFINITY_I:  {self.CharClass.LOW_N: self.State.NEGATIVE_INFINITY_N},
            self.State.NEGATIVE_INFINITY_N:  {self.CharClass.LOW_F: self.State.NEGATIVE_INFINITY_F},
            self.State.NEGATIVE_INFINITY_F:  {self.CharClass.LOW_I: self.State.NEGATIVE_INFINITY_I2},
            self.State.NEGATIVE_INFINITY_I2: {self.CharClass.LOW_N: self.State.NEGATIVE_INFINITY_N2},
            self.State.NEGATIVE_INFINITY_N2: {self.CharClass.LOW_I: self.State.NEGATIVE_INFINITY_I3},
            self.State.NEGATIVE_INFINITY_I3: {self.CharClass.LOW_T: self.State.NEGATIVE_INFINITY_T},
            self.State.NEGATIVE_INFINITY_T:  {
                self.CharClass.LOW_Y: self._transition_with_event(self.State.OK, "value_end", event_param=float('-inf'))
            },
            self.State.OK: {
                self.CharClass.SPACE: self.State.OK,
                self.CharClass.WHITESPACE: self.State.OK,
                self.CharClass.RIGHT_CURVED_BRACKET: self._right_curved_bracket_transition,
                self.CharClass.RIGHT_SQUARE_BRACKET: self._right_square_bracket_transition,
                self.CharClass.COMMA: self._comma_transition,
            }
        }

    def parse(self, gen):
        for data in gen:
            self._load(data)
            for event in self._parse_chunk():
                yield event

        if self.state != self.State.OK:
            for event in self._process_char('<end of data>', self.CharClass.END_OF_DATA):
                yield event
        elif not self._pop(self.Mode.DONE):
            self._raise_parse_error('<end of data>')

    def _load(self, data):
        """
        Load data chunk, checking for utf-8 BOM and decoding bytes.
        """

        self.local_index = 0

        if self.index == 0 and data.startswith('\ufeff'):
            self._raise_parse_error("<unexpected UTF-8 BOM>")

        if type(data) is bytes:
            self.data = data.decode("utf-8")
        else:
            self.data = data

    def _pop(self, mode):
        """
        Check top mode on stack and pop it.
        """

        if len(self.stack) == 0 or self.stack[-1] != mode:
            return False
        self.stack.pop()
        return True

    def _transition_with_event(self, state, event_name, event_param=None, use_token=False):
        """
        Transition to state while yielding an event.
        """

        if use_token:
            event_param = self.token

        def fun(slf, _):
            slf.state = state
            yield event_name, event_param

        return partial(fun, self)

    def _transition_with_token_accum(self, state):
        """
        Transition to state while accumulating passed char in token.
        """

        def fun(slf, ch):
            slf.token += ch
            slf.state = state
            yield from []

        return partial(fun, self)

    def _left_curved_bracket_transition(self, _):
        self.stack.append(self.Mode.KEY)
        self.state = self.State.OBJECT

        yield "object_start", None

    def _left_square_bracket_transition(self, _):
        self.stack.append(self.Mode.ARRAY)
        self.state = self.State.ARRAY

        yield "array_start", None

    def _empty_right_curved_bracket_transition(self, ch):
        if not self._pop(self.Mode.KEY):
            self._raise_parse_error(ch)

        self.state = self.State.OK

        yield "object_end", None

    def _right_curved_bracket_transition(self, ch):
        if not self._pop(self.Mode.OBJECT):
            self._raise_parse_error(ch)

        for evt_name, evt_param in self._yield_literal_event():
            yield evt_name, evt_param

        self.state = self.State.OK

        yield "object_end", None

    def _right_square_bracket_transition(self, ch):
        if not self._pop(self.Mode.ARRAY):
            self._raise_parse_error(ch)

        for evt_name, evt_param in self._yield_literal_event():
            yield evt_name, evt_param

        self.state = self.State.OK

        yield "array_end", None

    def _comma_transition(self, ch):
        if self.stack[-1] == self.Mode.OBJECT:
            for evt_name, evt_param in self._yield_literal_event():
                yield evt_name, evt_param

            self._pop(self.Mode.OBJECT)
            self.stack.append(self.Mode.KEY)
            self.state = self.State.ELEM_START

        elif self.stack[-1] == self.Mode.ARRAY:
            for evt_name, evt_param in self._yield_literal_event():
                yield evt_name, evt_param

            self.state = self.State.ELEM_START

        else:
            self._raise_parse_error(ch)

    def _colon_transition(self, ch):
        if not self._pop(self.Mode.KEY):
            self._raise_parse_error(ch)

        self.stack.append(self.Mode.OBJECT)
        self.state = self.State.ELEM_START

        yield from []

    def _quote_transition(self, ch):
        stack_top = self.stack[-1]
        if stack_top == self.Mode.KEY:
            token = self._decode_string_literal(ch)
            yield "object_key_end", token
            self.token = ''
            self.state = self.state.COLON
        elif stack_top in [self.Mode.OBJECT, self.Mode.ARRAY, self.Mode.DONE]:
            token = self._decode_string_literal(ch)
            yield "value_end", token
            self.token = ''
            self.state = self.state.OK
        else:
            self._raise_parse_error(ch)
            yield from []

    def _end_of_data_transition(self, ch):
        """
        "End of data" transition yielding a value_end for accumulated numeric literals.
        """
        if not self._pop(self.Mode.DONE):
            self._raise_parse_error(ch)

        for evt_name, evt_param in self._yield_literal_event():
            yield evt_name, evt_param

    def _numeric_literal_whitespace_transition(self, _):
        """
        Transition from numeric literal to whitespace, yielding a value_end event.
        """
        for evt_name, evt_param in self._yield_literal_event():
            yield evt_name, evt_param

        self.state = self.State.OK

    def _yield_literal_event(self):
        """
        Yield a value_end event if current state is "parsing numeric literal".
        """
        if self.state in [self.State.INT_LITERAL, self.State.INT_ZERO_LITERAL]:
            yield "value_end", int(self.token)
            self.token = ''

        elif self.state in [self.State.FLOAT_LITERAL, self.State.EXP_LITERAL]:
            yield "value_end", float(self.token)
            self.token = ''

        else:
            yield from []

    def _parse_chunk(self):
        """
        Parse currently loaded data chunk.
        """
        for ch in self.data:
            self.local_index += 1
            self.index += 1

            char_class = self.get_char_class(ch)
            for evt_name, evt_param in self._process_char(ch, char_class):
                yield evt_name, evt_param

    def _process_char(self, ch, char_class):
        """
        Process single char and transition to next state.

        :param ch: char
        :param char_class: char class
        """
        if char_class == self.CharClass.CONTROL:
            self._raise_parse_error(ch)

        next_state = self.transition_table[self.state].get(char_class, None)
        if next_state is None:
            self._raise_parse_error(ch)
        elif not callable(next_state):
            self.state = next_state
        else:
            for evt_name, evt_param in next_state(ch):
                yield evt_name, evt_param

    def _decode_string_literal(self, ch):
        """
        Decode string literal with json.loads.
        """

        token = ''
        try:
            token = json.loads('"' + self.token + '"')
        except json.decoder.JSONDecodeError:
            self._raise_parse_error(ch)

        return token

    def _raise_parse_error(self, ch):
        """
        Raise a parse error.

        :param ch: char on which parse error has occurred
        """
        raise ParseError("Parse error: unexpected char '{}' ({}) in state {} (local index {}, global index {})".format(
            ch,
            ord(ch) if len(ch) == 1 else "",
            self.state.name,
            self.local_index,
            self.index
          ))
