#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pip3 install fusepy
from stat import *
from fuse import FUSE, Operations, FuseOSError
from errno import ENOENT, EACCES
import os
import sys


class MergedFilesystem(Operations):
    """A FUSE filesystem that combines multiple folders into one folder with many symlinks to the actual files"""
    write = None

    def __init__(self, paths):
        print(f"Starting Merged Filesystem for paths: {paths}")
        for p in paths:
            print(f"    Path: {p}")

        self.paths = paths
    
    # Not needed because the files are never read, only the symlinks
    open = None
    read = None
    release = None

    def effective(self, path):
        """
        Return a list (maybe empty) of paths that would match the requested path
        Usually this list will only have one entry: The path where the file actually is
        The list can have multiple entries if the same file name exists at the same path in multiple source directories
        """
        def eff(p):
            return os.path.join(p, os.path.relpath(path, "/"))
        
        return [eff(p) for p in self.paths if os.path.exists(eff(p))]
        
    def readlink(self, path):
        """For all files, return their actual path as the link"""
        for p in self.effective(path):
            return p
        
        raise FuseOSError(ENOENT)

    def readdir(self, path, fh):
        """Return the combined result of listdir in all source directories. This may result in multiple files with the same name and path"""
        print(f"readdir(path={path}, fh={fh})")
        return (item for items in (os.listdir(p) for p in self.effective(path)) for item in items)

    def getattr(self, path, fh=None):
        """
        Return fake file attributes:
        The root folder attributes are not changed
        All other files and directories are readable and symlinks
        """
        print(f"getattr({self}, {path}, {fh})")

        for p in self.effective(path):
            s = os.stat(p)

            if path == "/":
                mode = s.st_mode
            elif os.path.isfile(p):
                mode = S_IFLNK | S_IRUSR| S_IRGRP | S_IROTH
            elif os.path.isdir(p):
                mode = S_IFLNK | S_IRUSR | S_IXUSR| S_IRGRP | S_IXGRP| S_IROTH | S_IXOTH
            else:
                raise FuseOSError(ENOENT)

            return {
                "st_mode": mode,
                "st_ctime": s.st_ctime,
                "st_mtime": s.st_mtime,
                "st_atime": s.st_atime,
                "st_nlink": s.st_nlink,
                "st_size": s.st_size
            }
        
        raise FuseOSError(ENOENT)

    def statfs(self, path):
        """The filesystem is read-only and has no free space"""
        print(f"statfs({self}, {path})")
        return dict(f_bsize=512, f_blocks=4096, f_bavail=0)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: %s <mountpoint> <src1> <src2> <src...> " % sys.argv[0])
        exit(1)

    fuse = FUSE(MergedFilesystem(sys.argv[2:]), sys.argv[1], foreground=True)