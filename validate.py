#!/usr/bin/env python3

import os

class Validate:
    @staticmethod
    def dir_writable(dnm: str) -> bool:
        if os.path.exists(dnm):
            # path exists
            if os.path.isdir(dnm): # is it a file or a dir?
                # also works when dir is a link and the target is writable
                return os.access(dnm, os.W_OK)
            else:
                return False # path is a file, so cannot write as a dir
        # target does not exist, check perms on parent dir
        pdir = os.path.dirname(dnm)
        if not pdir: pdir = '.'
        # target is creatable if parent dir is writable
        return os.access(pdir, os.W_OK)


    @staticmethod
    def file_readable(filename: str) -> bool:
        if os.path.exists(filename) and not os.path.isdir(filename):
            return os.access(filename, os.R_OK)
        return False


    @staticmethod
    def file_writable(filename: str) -> bool:
        if os.path.exists(filename):
            # path exists
            if not os.path.isdir(filename): # is it a file or a dir?
                # also works when file is a link and the target is writable
                return os.access(filename, os.W_OK)
            else:
                return False # path is a dir, so cannot write as a file
        # target does not exist, check perms on parent dir
        pdir = os.path.dirname(filename)
        if not pdir: pdir = '.'
        # target is creatable if parent dir is writable
        return os.access(pdir, os.W_OK)
