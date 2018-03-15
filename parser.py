#!/usr/bin/env python3.6

import os
import sys
import time
from abc import ABCMeta, abstractproperty
from io import BytesIO
from mmap import mmap, PROT_READ
from pathlib import Path

from PIL import Image

from packed_struct import F, Struct

MAX_MMAP = 2 * 1024 * 1024
OUT_DIR = Path("out").resolve()


class Command(Struct, metaclass=ABCMeta):
    @abstractproperty
    def CODE(self):
        """The byte string code for this command
        """
        raise NotImplementedError

    @abstractproperty
    def code(self):
        """The (F.bytes) field containing the code
        """
        raise NotImplementedError


class MoveVertPos(Command):
    CODE = b"\x1b*rY"

    code = F.bytes(len(CODE), allowed={CODE})
    n_dots = F.ubyte()
    null = F.ubyte(allowed={0})


class StartRow(Command):
    CODE = b"b"

    code = F.bytes(len(CODE), allowed={CODE})
    n_bytes = F.uint16le()


def find_commands(buff, command_cls, start_offset=0, end_offset=-1):
    if end_offset == -1 or end_offset is None:
        end_offset = len(buff)

    if isinstance(start_offset, Command):
        start_offset = start_offset._offset + start_offset._size
    if isinstance(end_offset, Command):
        end_offset = end_offset._offset

    offset = buff.find(command_cls.CODE, start_offset)
    while start_offset <= offset < end_offset:
        yield command_cls(buff, offset)
        offset = buff.find(command_cls.CODE, offset + 1)


def with_next(iterable):
    it = iter(iterable)
    prev = next(it)
    try:
        while True:
            curr = next(it)
            yield (prev, curr)
            prev = curr

    except StopIteration:
        yield (prev, None)


def read_images(filename):
    filesize = os.stat(filename).st_size

    with open(filename) as _, mmap(_.fileno(), min(MAX_MMAP, filesize), prot=PROT_READ) as doc:
        for current, nxt in with_next(find_commands(doc, MoveVertPos)):
            image = []
            for start_row in find_commands(doc, StartRow, current, nxt):
                row_offset = start_row._offset + start_row._size
                image.append(doc[row_offset:row_offset + start_row.n_bytes])

            yield image


def dumpimage(data, outpath):
     size = (max(map(len, data)), len(data))
     image = bytearray(size[0] * size[1])
     for ii in range(size[1]):
         image[ii*size[0]:ii*size[0]+min(size[0], len(data[ii]))] = data[ii]
     Image.frombytes("1", (size[0]*8, size[1]), bytes(image), "raw", "1;I").save(outpath)


def main(filename):
    now = str(int(time.time()))
    outdir = OUT_DIR / now
    outdir.mkdir(exist_ok=True, parents=True)
    print("Dumping to '{}'".format(outdir))

    for idx, image in enumerate(read_images(filename), 1):
        if image and image[0]:
            dumpimage(image, outdir / "{:d}.bmp".format(idx))



if __name__ == "__main__":
    main(sys.argv[1])
