#!/usr/bin/env python3

"""Draw an image showing usage of disk block by block"""

import math
import re
import subprocess

from PIL import Image

WHITE = bytes([0xff])
BLACK = bytes([0x00])
BLUE = bytes([0xcc])
GREEN = bytes([0x88])
YELLOW = bytes([0x44])


def parse_block_list(string, group_base=0):
    """Parse a block list string"""
    ret = []
    args = string.split(',')
    for arg in args:
        arg = arg.strip()
        if not arg:
            # Discard empty free lists
            pass
        elif '-' in arg:
            # Range of blocks
            ret.append([int(x) + group_base for x in arg.split('-')])
        else:
            # Single block
            ret.append([int(arg) + group_base, int(arg) + group_base])
    return ret


def parse_line(line, group_base):
    """Parse a single line from the blockdev information"""
    ret = {}

    match = re.match(r'.*superblock at ([0-9]*).*', line)
    if match:
        ret['superblocks'] = parse_block_list(match[1])

    match = re.match(r'.*Group descriptors at ([0-9-]*).*', line)
    if match:
        ret['group_descriptors'] = parse_block_list(match[1], group_base)

    match = re.match(r'.*bitmap at ([0-9-]*).*', line)
    if match:
        ret['group_descriptors'] = parse_block_list(match[1], group_base)

    match = re.match(r'.*Inode table at ([0-9-]*).*', line)
    if match:
        ret['inode_tables'] = parse_block_list(match[1], group_base)

    match = re.match(r'Free blocks: ([0-9-, ]*)', line)
    if match:
        ret['free_blocks'] = parse_block_list(match[1])

    return ret


def parse_disk(blockdev):
    """Parse the disk usage information out of a blockdev
       blockdv must be formatted as ext? filesystem
    """
    dump = subprocess.check_output(["sudo", "dumpe2fs", blockdev])
    ret = {
        'total_blocks': None,
        'free_blocks': [],
        'superblocks': [],
        'group_descriptors': [],
        'inode_tables': [],
    }
    group_base = None
    for line in dump.splitlines():
        line = line.decode("utf-8").strip()

        if line.startswith("Block count:"):
            ret['total_blocks'] = int(line.split(':')[1].strip())

        match = re.match(r'^Group [0-9]*: \(Blocks ([0-9]*).*', line)
        if match:
            group_base = int(match[1])

        parsed = parse_line(line, group_base)
        for key, value in parsed.items():
            ret[key] += value

    return ret


def set_pixels(data, blocks, color):
    """Set a range of pixels in the provided bytearray to the specified color"""
    start = blocks[0]
    end = blocks[1]
    length = end - start + 1
    data[start:end] = color*length


def gen_image(parsed):
    """Generate an image representing the disk"""
    # Scale to 16:9
    width = int(math.sqrt(parsed['total_blocks'] * 16 / 9))
    height = int(parsed['total_blocks'] / width)

    data = bytearray(parsed['total_blocks'])

    for block in parsed['free_blocks']:
        set_pixels(data, block, WHITE)

    for block in parsed['superblocks']:
        set_pixels(data, block, BLUE)

    for block in parsed['group_descriptors']:
        set_pixels(data, block, GREEN)

    for block in parsed['inode_tables']:
        set_pixels(data, block, YELLOW)

    image = Image.frombytes('P', [width, height], bytes(data))

    return image


def main():
    """Main"""
    import json
    import sys

    data = parse_disk(sys.argv[1])
    print(json.dumps(data, indent=2))
    image = gen_image(data)
    print(image)
    image.show()


if __name__ == '__main__':
    main()
