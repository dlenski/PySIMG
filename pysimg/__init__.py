from enum import IntEnum

class SparseChunkType(IntEnum):
    RAW = 0xCAC1
    FILL = 0xCAC2
    DONT_CARE = 0xCAC3
    CRC32 = 0xCAC4

from .writer import SimgWriter
