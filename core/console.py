#!/usr/bin/env python3
# coding=utf-8

"""
Copyright (c) 2019 mullaihub developers (https://www.mullaihub.com/accng)
See the file 'LICENSE' for copying permission
"""

from core.cmd import Cmd
import sqlite3
import os

try:
    import readline
except:
    readline = None

from util.colorify import green, underline
from util import log
from cmd import Cmd


class Console(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        self.histfile = os.path.expanduser('~/.accng')
        self.histfile_size = 1000
        self.prompt = "{} → ".format(underline(green("accng")))

    def preloop(self):
        if readline and os.path.exists(self.histfile):
            readline.read_history_file(self.histfile)

    def postloop(self):
        if readline:
            readline.set_history_length(self.histfile_size)
            readline.write_history_file(self.histfile)

    def do_db(self, line):
        """db <operation>"""
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        
        c.close()
        conn.close()

    def do_exit(self, line):
        """quit out of accng"""
        return True

    def default(self, line):
        log.info("Exec: {}\n".format(line))
        os.system(line)