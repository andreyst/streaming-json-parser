import resource
from decoder import Decoder
import time
import json

class EffectiveDecoder(Decoder):
    """
    Decodes a json with scheme [ elem, elem, ... ] in a streaming fashion
    """

    def decode(self):
        # Look for array beginning
        evt_name, evt_param = next(self.parser_gen)
        if evt_name != "array_start":
            raise ValueError("Json does not start with an array")

        # Iterate for every element in array
        while True:
            # Collect single element
            # It is not stored anywhere, greatly reducing memory footprint
            is_data, value = self._parse_sub_tree()

            if not is_data:
                break


def data_gen():
    yield "["
    for i in range(2000):
        yield '{"a":1000},'
    yield "0]"


def full_data_gen():
    str = "[" + '{"a":1000},' * 20000 + "0]"
    yield str


def main():
    datum = [
        "true",
        "100",
        "[1,2,true]",
        '"\\u4e16\\u754c"',
        'NaN',
        'true',
        'false',
        'null',
        'Infinity',
        '-Infinity',
        '1.00',
        '1e2',
        '1e-2',
        '1.34e+3',
        '{}',
        '{"a":2}',
        '["spam"',
        '[  ]'
        # [ data_gen ]
      # ['"spam']
      # ['[' * 100000 + '1' + ']' * 100000],
      # ['["line\\\nbreak"]'],
      # ["0.0","0"],
      # ["0"],
      # ["0.000"],
      # ['[1,2,]'],
      # ['{}'],
      # ['{"a":[]}'],
      # [r'{ "a": "\u0123\u4567\u89ab\ucd" }'],
      # [r'\h'],
      # ['{"Extra value after close": true} "misplaced quoted value"']
      # ['false'],
      #  ['true'],
      # ['NaN'],
      # ['null'],
      # ['-Infinity'],
      # ['Infinity'],
      # ['-1.0003e2']
      # ['{ "x": {"a":"b"}, "e":2,"f":3,"y":{"a":{"b":"c"}} }'],
      # ['[-1]'],
      # ['[1,{"a":"b"},2,3,{"a":{"b":"c"}}]'],
      # ['[{},{},{}]'],
      # [
      #   '[{},{},{},',
      #   '{"111":"222"},',
      #   '{"vvv":"vv',
      #   """
      #     vvvvv",
      #     "a": [ {"asd":"ads"}, {"zzc":"zxc"} ],
      #     "b": [
      #   """,
      #   """
      #   { "asdaasd": "zxczxc" }
      #   """,
      #   ",1,2,3]",
      #   "}]"
      # ],
    ]

    for data in datum:
        print("source data: '{}'".format(data))
        decoder = Decoder(data)
        d = decoder.decode()
        print("decoded data:")
        print(d)
        # print("len of decoded data: {}".format(len(d)))

    # decoder = Decoder(data_gen())
    # d = decoder.decode()
    # print(len(d))

    # start = time.time()
    # decoder = EffectiveDecoder(full_data_gen())
    # decoder.decode()
    # elapsed_time = time.time() - start
    # print("EffectiveDecoder took {:.3f}s".format(elapsed_time))

    # start = time.time()
    # json.loads(s)
    # elapsed_time = time.time() - start
    # print("JsonDecoder took {:.3f}s".format(elapsed_time))


    # s = ""
    # for d in data_gen():
    #     s += d
    # json.loads(s)

    print(resource.getrusage(resource.RUSAGE_SELF))
      # print(json.dumps(decoder.decode()))
    # for data in datum:
    # parse(d for d in datum[0])

    # r = requests.get('http://localhost:8000/', stream=True)
    # gen = r.iter_content(chunk_size=100)
    # decoder = Decoder(gen)
    # print(decoder.decode())

    # r = requests.get('http://localhost:8000/', stream=True)
    # res = bytearray()
    # try:
    #   i =
    #   while True:
    #     c = next(i)
    #     res.extend(c)
    # except StopIteration as err:
    #   pass
    # print(json.loads(res))


if __name__ == "__main__":
    main()
