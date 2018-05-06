# -*- coding: utf-8 -*-

from decoder import Decoder
import json
import time
import math
from naya import parse_string
# from yajl import YajlParser
from jsonstreamer import JSONStreamer


def streaming(data):
    decoder = Decoder(d for d in [data])
    decoder.decode()


def python(data):
    json.loads(data)


def naya(data):
    parse_string(data)


def yajl(data):
    parser = YajlParser()
    parser.parse(data)


def jsonstreamer(data):
    streamer = JSONStreamer()
    # streamer.add_catch_all_listener(lambda x: x)
    streamer.consume(data)  # note that partial input is possible
    streamer.close()


def main():
    parsers = {
        'streaming': streaming,
        'python': python,
        'naya': naya,
        'jsonstreamer': jsonstreamer,
    }
    results = {k: [] for k in parsers.keys()}

    data = '[' + ('{"a":1},' * 10000) + '0]'

    for k, parser in parsers.items():
        for i in range(10):
            start = time.time()
            parser(data)
            elapsed = time.time() - start
            results[k].append(elapsed)

    print("{:10s} | min   | max   | avg   | stddev ")

    for name, r in results.items():
        r.sort()
        for i in range(3):
            r.pop()

        mean = float(sum(r)) / max(len(r), 1)
        dist = 0
        for num in r:
            dist += (num - mean) ** 2
        stddev = math.sqrt(dist / max(len(r), 1))
        print("{} | {:.3f} | {:.3f} | {:.3f} | {:.3f}".format(name, r[0], r[-1], mean, stddev))


if __name__ == '__main__':
    main()
