#!/usr/bin/env python2
from __future__ import print_function, division
from sys import stderr, stdout
from functools import partial
from binascii import hexlify
from enum import IntEnum
from struct import pack, unpack, calcsize
from os import SEEK_CUR, SEEK_END, SEEK_SET, fstat
import stat
import argparse

class SparseChunkType(IntEnum):
    RAW = 0xCAC1
    FILL = 0xCAC2
    DONT_CARE = 0xCAC3
    CRC32 = 0xCAC4

class SimgWriter(object):
    file_header = "<I4H4I"
    chunk_header = "<2H2I"
    file_header_size = calcsize(file_header)
    chunk_header_size = calcsize(chunk_header)

    def __init__(self, outf, blocksize = 4096, debug = 0):
        assert blocksize > 0
        assert blocksize % 4 == 0

        self.outf = outf
        self.blocksize = blocksize
        self.debug = debug

        self.nchunks = 0         # number of chunks written
        self.nblocks = 0         # number of blocks of data added

        self.ctype = None        # SparseChunkType of current chunk
        self.cval = None         # fill or CRC32 value for current chunk
        self.csize = 0           # number of blocks in current chunk
        self.buf = b''

        # leave room for file header
        outf.write(b'\0' * self.file_header_size)

    def tell(self):
        return self.outf.tell()

    def _print_state(self, pfx, debug):
        if self.debug >= debug:
            print("%snchunks=%d, nblocks=%d, ctype=%s, cval=%r, csize=%d, len(buf)=%d, tell()=%d" %
                  (pfx, self.nchunks, self.nblocks, self.ctype and self.ctype.name, self.cval, self.csize, len(self.buf), self.tell()),
                  file=stderr)

    def close(self):
        if self.buf:
            raise RuntimeError('%d leftover bytes (data written must be a multiple of blocksize %d)' % (len(self.buf), self.blocksize))

        # write final unwritten chunk
        self._close_chunk()

        self.outf.seek(0, SEEK_SET)
        self._print_state('  writing final header: ', 1)
        self.outf.write( pack(self.file_header,
                              0xED26FF3A, # magic
                              1, 0, # version 1.0
                              self.file_header_size, self.chunk_header_size, self.blocksize, self.nblocks, self.nchunks,
                              0 # checksum
                              ))
        self.outf.seek(0, SEEK_END)

    def _close_chunk(self):
        self._print_state('   top of _close_chunk: ', 1)

        if self.csize == 0:
            return

        if self.ctype == SparseChunkType.RAW:
            databytes = self.csize * self.blocksize
            self.outf.seek(- databytes - self.chunk_header_size, SEEK_CUR) # return to where chunk header belongs
        elif self.ctype == SparseChunkType.DONT_CARE:
            databytes = 0
        else:
            databytes = len(self.cval)

        self.outf.write( pack(self.chunk_header, self.ctype, 0, self.csize, self.chunk_header_size + databytes) )

        if self.ctype == SparseChunkType.RAW:
            self.outf.seek(0, SEEK_END) # go back to end of file
        elif self.ctype == SparseChunkType.DONT_CARE:
            pass
        else:
            self.outf.write(self.cval)

        self.csize = 0
        self.nchunks += 1

        self._print_state('bottom of _close_chunk: ', 1)

    def _add_data_block(self):
        self._print_state('   top of _add_data_block: ', 2)

        block = self.buf
        assert len(block) == self.blocksize

        # determine correct chunk type
        cval = block[:4]
        if block == cval * (self.blocksize//4):
            ctype = SparseChunkType.FILL
        else:
            ctype = SparseChunkType.RAW
            cval = None

        # if chunk type is changing, close out the current chunk
        if self.ctype != ctype or self.cval != cval:
            self._close_chunk()

        # write data for raw chunks immediately, leaving room for chunk header if we just changed
        if ctype == SparseChunkType.RAW:
            if ctype != self.ctype:
                self.outf.write(b'\0' * self.chunk_header_size)
            self.outf.write(block)

        self.ctype = ctype
        self.cval = cval
        self.csize += 1
        self.nblocks += 1
        self.buf = b''

        self._print_state('bottom of _add_data_block: ', 2)

    def write(self, data):
        nblocks = pp = 0

        if self.buf:
            pp = self.blocksize - len(self.buf)
            self.buf += data[:pp]
            if len(self.buf) == self.blocksize:
                self._add_data_block()
                nblocks += 1

        for pp in range(pp, len(data), self.blocksize):
            self.buf = data[pp : pp+self.blocksize]
            if len(self.buf) == self.blocksize:
                self._add_data_block()
                nblocks += 1

        return nblocks

p = argparse.ArgumentParser()
p.add_argument('img', type=argparse.FileType('rb'))
p.add_argument('-b', '--blocksize', default=4096, type=int, help='Sparse block size (default %(default)s)')
p.add_argument('-o', '--output', type=argparse.FileType('wb'), default=stdout, help='Output file (default is standard output)')
p.add_argument('-d', '--debug', action='count', default=0)
args = p.parse_args()

st = fstat(args.img.fileno())
if stat.S_ISREG(st.st_mode):
    if st.st_size % args.blocksize != 0:
        p.error('Image size is not an exact multiple of --blocksize %d' % args.blocksize)
    img_total_blocks = st.st_size // args.blocksize
else:
    img_total_blocks = None
    print('WARNING: Image is not a regular file; cannot verify that it is an exact multiple of --blocksize %d' % args.blocksize, file=stderr)

with args.output:
    wr = SimgWriter(args.output, blocksize=args.blocksize, debug=args.debug)
    for block in iter( partial(args.img.read, args.blocksize), b'' ):
        wr.write(block)
    wr.close()

    print('Wrote %d blocks in %d sparse chunks (%d%% compression)' % (wr.nblocks, wr.nchunks, (args.output.tell()/(nblocks*args.blocksize))*100), file=stderr)
    if img_total_blocks is not None:
        assert wr.nblocks == img_total_blocks
