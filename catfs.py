#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pip3 install fusepy
from stat import S_IFDIR, S_IFLNK, S_IFREG
from fuse import FUSE, Operations, FuseOSError
from errno import ENOENT
from time import time
import sys


class CatFilesystem(Operations):
    open = None
    write = None

    def __init__(self):
        with open("cat.jpg", "rb") as f:
            self.cat = f.read()

        self.meow = b"Meow!"

        self.touched = set()

        self.rootfile = dict(st_mode=(S_IFDIR | 0o755), st_nlink=2)
        self.catfile = dict(st_mode=(S_IFREG | 0o777), st_nlink=1, st_size=len(self.cat))
        self.meowfile = dict(st_mode=(S_IFREG | 0o777), st_nlink=1, st_size=len(self.meow))

    def read(self, path, size, offset, fh):
        print(path, size, offset, fh)
        if path == "/.debug":
            data = "I know these files: " + ", ".join(self.touched) + "\n"
        else:
            data = self.cat if path.endswith("jpg") else self.meow
        return data[offset:offset + size]

    def readdir(self, path, fh):
        return ['.', '..'] + list(self.touched)

    def getattr(self, path, fh=None):
        if path == "/":
            return self.rootfile
        else:
            self.touched.add(path.strip("/"))
            if path == "/.debug":
                print(path)
                return dict(st_mode=(S_IFREG | 0o777), st_nlink=1, st_size=len(str(self.touched)))
            if path.endswith("jpg"):
                return self.catfile
            else:
                return self.meowfile

    def statfs(self, path):
        return dict(f_bsize=512, f_blocks=4096, f_bavail=0)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('usage: %s <mountpoint>' % sys.argv[0])
        exit(1)

    fuse = FUSE(CatFilesystem(), sys.argv[1], foreground=True)
