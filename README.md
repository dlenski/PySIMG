pysimg
======

Pure-python tools for handling Android
[`fastboot`](https://en.wikipedia.org/wiki/Android_software_development#Fastboot)'s [sparse image
format](http://www.2net.co.uk/tutorial/android-sparse-image-format).

Essentially, the sparse image format is a _very simple_ form of compression which can skip
over unpopulated space in images (`DONT_CARE`) or repeated 4-byte sequences (`FILL`).

`img2simg.py`
=============

img2simg converts raw disk images to Android's sparse image format. Features:

* Unlike [the official `img2simg`](https://android.googlesource.com/platform/system/core/+/master/libsparse/img2simg.c),
  this version doesn't `seek` in the input file, so it can be used (for example) to sparsify a
  raw disk image streamed from a decompression.
* It can split images into multiple sparse images of no more than a certain size
  (specified in [MiB](https://en.wikipedia.org/wiki/Mebibyte) with `--split MiB`).
  Each of the images is pre- and post-padding with `DONT_CARE` blocks, to
  align with the full image size. (The only other publicly-available tool I know of that can do this
  is [SparseConverter](https://forum.xda-developers.com/showthread.php?t=2749797)).

Available options:

```
usage: img2simg.py [-h] [-b BLOCKSIZE] [-o OUTPUT] [-S MiB] [-d] img

positional arguments:
  img

optional arguments:
  -h, --help            show this help message and exit
  -b BLOCKSIZE, --blocksize BLOCKSIZE
                        Sparse block size (default 4096)
  -o OUTPUT, --output OUTPUT
                        Output file (default is standard output)
  -S MiB, --split MiB   Split output into multiple sparse images of no more
                        than the specified size in MiB (= 2**20 bytes)
  -d, --debug
```

Author
------
&copy; Daniel Lenski <<dlenski@gmail.com>> (2014-2016)

License
-------
[GPL v3 or later](http://www.gnu.org/copyleft/gpl.html)
