#!/usr/bin/env python2
from __future__ import print_function, division
from sys import stderr, stdout
from functools import partial
from binascii import unhexlify
from os import fstat
import stat
import argparse

from .writer import SimgWriter

def power_of_2(val):
    num = int(val)
    if num<256 or (num & (num-1)):
        raise ValueError
    return num

def hex_pattern(val):
    val = unhexlify(val)
    if len(val) not in (1,2,4):
        raise ValueError
    return val * (4//len(val))

def parse_args(args=None):
    p = argparse.ArgumentParser()
    p.add_argument('img', type=argparse.FileType('rb'))
    p.add_argument('-b', '--blocksize', default=4096, type=power_of_2, help='Sparse block size (default %(default)s)')
    p.add_argument('-o', '--output', default=stdout, metavar='PATH', help='Output file (default is standard output)')
    p.add_argument('-S', '--split', default=None, type=int, metavar='MiB', help='Split output into multiple sparse images of no more than the specified size in MiB (= 2**20 bytes)')
    p.add_argument('-D', '--dont-care', default=[], action='append', type=hex_pattern, metavar='PATTERN', help='Hex pattern (e.g. FFFFFFFF) to treat as DONT_CARE; may be specified multiple times')
    p.add_argument('-d', '--debug', action='count', default=0)
    args = p.parse_args()

    if args.split and not isinstance(args.output, str):
        p.error('Must specify output filename prefix with --output to write split sparse images')

    return p, args

def main():
    p, args = parse_args()

    st = fstat(args.img.fileno())
    if stat.S_ISREG(st.st_mode):
        if st.st_size % args.blocksize != 0:
            p.error('Image size is not an exact multiple of --blocksize %d' % args.blocksize)
        img_total_blocks = st.st_size // args.blocksize
    else:
        img_total_blocks = None
        print('WARNING: Image is not a regular file; cannot verify that it is an exact multiple of --blocksize %d' % args.blocksize, file=stderr)
        if args.split:
            print('         Cannot pad split files with DONT_CARE blocks to total block size.', file=stderr)

    start_block = split_number = 0
    done = False

    while not done:
        if args.split:
            outf = open(args.output + '.split_%d' % split_number, 'wb')
        elif isinstance(args.output, str):
            outf = open(args.output, 'wb')
        else:
            outf = args.output

        with SimgWriter(outf, blocksize=args.blocksize, debug=args.debug, start_block_offset=start_block, end_block_offset=img_total_blocks, dont_care=args.dont_care) as wr:
            for nb, block in enumerate(iter( partial(args.img.read, args.blocksize), b'' )):
                wr.write(block)

                if args.split and ((wr.tell()+args.blocksize)>>20) >= args.split:
                    # writing one more block (might) exceed desired split size in MiB...
                    break
            else:
                # we only reach this when we run out of input "naturally"...
                done = True

            wr.flush()
            print('%s: Wrote %d blocks in %d sparse chunks (%d%% compression)' % (outf.name, nb, wr.nchunks, (wr.tell()/(nb*args.blocksize))*100), file=stderr)

            start_block += nb
            split_number += 1

if __name__=='__main__':
    main()
