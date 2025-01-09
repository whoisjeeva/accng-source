#!/usr/bin/env python3
# coding=utf-8

"""
Copyright (c) 2019 mullaihub developers (https://www.mullaihub.com/accng)
See the file 'LICENSE' for copying permission
"""

from core.module import Plugin
from util import log


class AccngPlugin(Plugin):
    def __init__(self, module):
        Plugin.__init__(self, module)
        self.name = "Example Plugin"
        self.description = "This is an example Plugin"
        self.author = ["Jeeva"]
        self.options.add("name", "", "Your name")

    def run(self):
        self.module.test = "This is set by plugin"
        name = self.options.get("name")
        log.info(f"Running plugin with name: {name}")