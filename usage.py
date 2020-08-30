#!/usr/bin/env python3

"""Draw an image showing usage of disk block by block"""

import math
import re
import subprocess
import sys

from PIL import Image
import hilbert_curve


def build_palette():
    """Build a palette of rgb colors"""
    palette = [
        0x00, 0x00, 0x00,  # Black image border
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
    'border': 0,
    'used_blocks': 1,
    'free_blocks': 2,
    'superblocks': 3,
    'group_descriptors': 4,
    'inode_tables': 5,
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
    if blockdev == '-':
        dump = sys.stdin.read()
    else:
        dump = subprocess.check_output(
            ["sudo", "dumpe2fs", blockdev]).decode("utf-8")
    total_blocks = None
    ret = {
        'free_blocks': [],
        'superblocks': [],
        'group_descriptors': [],
        'inode_tables': [],
    }
    group_base = None
    for line in dump.splitlines():
        line = line.strip()

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


def hilbert_convert(data_linear):
    """Map the data in data_linear into a hilbert curve."""

    total_blocks = len(data_linear)

    # Scale to contain a hilbert curve
    m = 1
    while (2**m) * 2 < total_blocks:
        m += 1
    pixels = (2**m) * 2

    width = int(math.sqrt(pixels))
    height = width

    data = bytearray(pixels)
    set_pixels(data, (0, pixels-1), COLOR_KEY['border'])
    for i, byte in zip(range(len(data_linear)), data_linear):
        x, y = hilbert_curve.d2xy(m, i)
        index = (y * width) + x
        data[index] = byte

    return data, width, height


def gen_image(total_blocks, parsed):
    """Generate an image representing the disk"""
    data_linear = bytearray(total_blocks)
    set_pixels(data_linear, (0, total_blocks-1), COLOR_KEY['used_blocks'])

    for key in parsed.keys():
        for block in parsed[key]:
            set_pixels(data_linear, block, COLOR_KEY[key])

    data, width, height = hilbert_convert(data_linear)

    image = Image.frombytes('P', [width, height], bytes(data))
    image.putpalette(PALETTE)

    return image


def main():
    """Main"""
    if len(sys.argv) < 2:
        raise Exception(
            "Usage: {} [partition] [(optional)filename.png]".format(
                sys.argv[0]))

    total_blocks, parsed = parse_disk(sys.argv[1])
    image = gen_image(total_blocks, parsed)

    if len(sys.argv) > 2:
        image.save(sys.argv[2])
    else:
        image.show()


if __name__ == '__main__':
    main()
