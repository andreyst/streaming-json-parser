# -*- coding: utf-8 -*-

from decoder import Decoder
import json
import time
import math


def streaming(data):
    decoder = Decoder(d for d in [data])
    decoder.decode()


def python(data):
    json.loads(data)


def main():
    parsers = {
        'streaming': streaming,
        'python': python,
    }
    results = {k: [] for k in parsers.keys()}
    print(results)

    data = ['[' + ('{"a":1},' * 20000) + '0]']

    for k, parser in parsers.items():
        start = time.time()
        parser(data[0])
        elapsed = time.time() - start
        results[k].append(elapsed)

    for name, r in results.items():
        r.sort()
        for i in range(3):
            r.pop()

        mean = float(sum(r)) / max(len(r), 1)
        dist = 0
        for num in r:
            dist += (num - mean) ** 2
        stddev = math.sqrt(dist / max(len(r), 1))
        print("{} min/max/avg/stddev: {:.3f}/{:.3f}/{:.3f}/{:.3f}".format(name, r[0], r[-1], mean, stddev))


if __name__ == '__main__':
    main()
