#!/usr/bin/env python3
import struct
from Xlib import X
from PIL import Image, ImageDraw
import subprocess
import argparse
from pathlib import Path
import shutil

# portions of this code taken from
# https://github.com/alexer/python-xlib-render/blob/master/xcursor.py

def chunk(data, size):
    assert size <= len(data)
    return data[:size], data[size:]

def unpack(data, size, fmt):
    this, rest = chunk(data, size)
    return struct.unpack(fmt, this), rest

def parse_cursor(data):
    magic, data = chunk(data, 4)
    assert magic == b'Xcur'

    (header_size, version, toc_count), data = unpack(data, 12, '<III')
    #print 'HDR: size, version, count =', (header_size, version, toc_count)
    assert header_size == 16

    tocs = []
    for i in range(toc_count):
        item, data = unpack(data, 12, '<III')
        type, subtype, position = item
        tocs.append(item)
        #print 'TOC: type, subtype, position =', item

    assert tocs[0][2] == header_size + toc_count * 12

    imgs = []
    pos = header_size + toc_count * 12
    for toc_type, toc_subtype, toc_position in tocs:
        assert toc_position == pos

        item, data = unpack(data, 16, '<IIII')
        header_size, type, subtype, version = item
        #print 'CHUNK: size, type, subtype, version =', item

        assert header_size == {0xfffe0001: 20, 0xfffd0002: 36}[type]
        assert toc_type == type
        assert toc_subtype == subtype

        if type == 0xfffe0001:
            assert subtype in (1, 2, 3)
            assert version == 1
            item, data = unpack(data, 4, '<I')
            length, = item
            string, data = chunk(data, length)
            #print 'STR:', repr(string)
        if type == 0xfffd0002:
            assert version == 1
            item, data = unpack(data, 20, '<IIIII')
            width, height, xhot, yhot, delay = item
            #print 'IMG: width, height, xhot, yhot, delay =', item
            assert width <= 0x7fff
            assert height <= 0x7fff
            assert xhot <= width
            assert yhot <= height
            length = width * height * 4
            pixels, data = chunk(data, length)
            imgs.append((width, height, xhot, yhot, delay, pixels))

        pos += header_size + length

    assert len(data) == 0

    return imgs


def highlight_cursor(src_cursor, radius, xhot, yhot):
    size = radius * 2
    img = Image.new('RGBA', (size, size), '#00000000')
    draw = ImageDraw.Draw(img)
    #p = (size - src_cursor.width)//2 - 1
    draw.ellipse([(0, 0), (size-1, size-1)], fill='#'+args.color)
    img.alpha_composite(src_cursor, (radius-xhot-1, radius-yhot-1))
    return img, radius-1, radius-1

def process_cursor(fpath, outfile):
    data = open(fpath, 'rb').read()
    cfg = []
    for (width, height, xhot, yhot, delay, pixels) in parse_cursor(data):
        img = Image.frombytes('RGBA', (width, height), pixels)
        new_width = int(args.scale*width)
        assert not new_width % 2
        hi_img, new_xhot, new_yhot = highlight_cursor(
            img, new_width, xhot, yhot)
        fpath = "/tmp/cursor{}.png".format(width)
        hi_img.save(fpath)
        cfg.append("{} {} {} {} {}".format(
            new_width, new_xhot, new_yhot, fpath, delay))
    # run xcursorgen
    cfg = "\n".join(cfg).encode('latin1')
    subprocess.run(['xcursorgen', '-', outfile], input=cfg, check=True)

def main():
    out_dir = Path(args.output_dir[0])
    for cursor in Path(args.input_dir).glob('*'):
        target = out_dir/cursor.name
        if cursor.is_symlink():
            shutil.copyfile(cursor, target, follow_symlinks=False)
        else:
            process_cursor(cursor, target)

def parse_args():
    parser = argparse.ArgumentParser(
        description='Generates highlighted X11 cursors.')
    parser.add_argument('output_dir',nargs=1,
                    help='cursor output directory')
    parser.add_argument('--input-dir',
                    default='/usr/share/icons/DMZ-White/cursors/',
                    help='path to cursors')
    parser.add_argument('--scale', type=float, default=1.25,
                    help='highlight scale [1.25]')
    parser.add_argument('--color', default='ffff008f',
                    help='highlight color rrggbbaa')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    main()
           
