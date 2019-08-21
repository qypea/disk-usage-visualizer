#!/usr/bin/env python3

"""Draw an image showing usage of disk block by block"""

import math
import re
import subprocess

from PIL import Image


def build_palette():
    """Build a palette of rgb colors"""
    palette = [
        0x80, 0x80, 0x80,  # Gray used blocks
        0xff, 0xff, 0xff,  # White free blocks
        0x00, 0x00, 0xff,  # Blue superblocks
        0x00, 0xff, 0x00,  # Green group descriptors
        0xff, 0xff, 0x00,  # Yellow inode tables
    ]
    while len(palette) < 768:
        palette.append(0)

    return palette


PALETTE = build_palette()

COLOR_KEY = {
    'free_blocks': 1,
    'superblocks': 2,
    'group_descriptors': 3,
    'inode_tables': 4,
}


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
    total_blocks = None
    ret = {
        'free_blocks': [],
        'superblocks': [],
        'group_descriptors': [],
        'inode_tables': [],
    }
    group_base = None
    for line in dump.splitlines():
        line = line.decode("utf-8").strip()

        if line.startswith("Block count:"):
            total_blocks = int(line.split(':')[1].strip())

        match = re.match(r'^Group [0-9]*: \(Blocks ([0-9]*).*', line)
        if match:
            group_base = int(match[1])

        parsed = parse_line(line, group_base)
        for key, value in parsed.items():
            ret[key] += value

    return total_blocks, ret


def set_pixels(data, blocks, color):
    """Set a range of pixels in the provided bytearray to the specified color"""
    start = blocks[0]
    end = blocks[1]
    length = end - start + 1
    data[start:end] = [color]*length


def gen_image(total_blocks, parsed):
    """Generate an image representing the disk"""
    # Scale to 16:9
    width = int(math.sqrt(total_blocks * 16 / 9))
    height = int(total_blocks / width)

    data = bytearray(total_blocks)

    for key in parsed.keys():
        for block in parsed[key]:
            set_pixels(data, block, COLOR_KEY[key])

    image = Image.frombytes('P', [width, height], bytes(data))
    image.putpalette(PALETTE)

    return image


def main():
    """Main"""
    import json
    import sys

    total_blocks, parsed = parse_disk(sys.argv[1])
    print(json.dumps(parsed, indent=2))
    image = gen_image(total_blocks, parsed)
    print(image)
    image.show()


if __name__ == '__main__':
    main()
