#!/usr/bin/env python3

"""Draw an image showing usage of disk block by block"""

import math
import subprocess
from PIL import Image

WHITE = bytes([0xff])
BLACK = bytes([0x00])


def parse_disk(blockdev):
    """Parse the disk usage information out of a blockdev
       blockdv must be formatted as ext? filesystem
    """
    dump = subprocess.check_output(["sudo", "dumpe2fs", blockdev])
    ret = {
        'total_blocks': None,
        'free_blocks': [],
    }
    for line in dump.splitlines():
        line = line.decode("utf-8").strip()

        if line.startswith("Block count:"):
            if ret['total_blocks'] is not None:
                raise Exception("Multiple 'Block Count' lines in dump")
            ret['total_blocks'] = int(line.split(':')[1].strip())

        if line.startswith('Free blocks:'):
            args = line.split(':')[1].strip().split(',')
            for arg in args:
                arg = arg.strip()
                if not arg:
                    # Discard empty free lists
                    continue

                if '-' not in arg:
                    # Normalize any entries which are a single block
                    arg = arg + '-' + arg
                ret['free_blocks'].append(arg)

    return ret


def set_pixels(data, blocks, color):
    """Set a range of pixels in the provided bytearray to the specified color"""
    start = int(blocks.split('-')[0])
    end = int(blocks.split('-')[1])
    length = end - start
    data[start:end] = color*length


def gen_image(parsed):
    """Generate an image representing the disk"""
    # Scale to 16:9
    width = int(math.sqrt(parsed['total_blocks'] * 16 / 9))
    height = int(parsed['total_blocks'] / width)

    data = bytearray(parsed['total_blocks'])

    for free in parsed['free_blocks']:
        set_pixels(data, free, WHITE)

    image = Image.frombytes('P', [width, height], bytes(data))

    return image


if __name__ == '__main__':
    import json
    import sys

    DATA = parse_disk(sys.argv[1])
    print(json.dumps(DATA, indent=2))
    IMAGE = gen_image(DATA)
    print(IMAGE)
    IMAGE.show()
