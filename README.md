pysimg
======

Pure-python tools for handling Android
[`fastboot`](https://en.wikipedia.org/wiki/Android_software_development#Fastboot)'s [sparse image
format](http://www.2net.co.uk/tutorial/android-sparse-image-format).

`img2simg.py`: converts raw disk images to sparse images. Features:

* Unlike [the official `img2simg`](https://android.googlesource.com/platform/system/core/+/master/libsparse/img2simg.c),
  this version doesn't `seek` in the input file, so it can be used (for example) to sparsify a
  raw disk image streamed from a decompression.
* It can split images into multiple sparse images of no more than a certain size
  (specified in [MiB](https://en.wikipedia.org/wiki/Mebibyte) with `--split MiB`).
  Each of the images is pre- and post-padding with `DONT_CARE` blocks, to
  align with the full image size. (The only other publicly-available tool I know of that can do this
  is [SparseConverter](https://forum.xda-developers.com/showthread.php?t=2749797)).

Author
------
&copy; Daniel Lenski <<dlenski@gmail.com>> (2014-2016)

License
-------
[GPL v3 or later](http://www.gnu.org/copyleft/gpl.html)
