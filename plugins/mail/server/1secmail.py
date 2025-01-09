#!/usr/bin/env python3
# coding=utf-8

"""
Copyright (c) 2019 mullaihub developers (https://www.mullaihub.com/accng)
See the file 'LICENSE' for copying permission
"""

from core.module import Plugin
from core.mail import OneSecMail
from util import log


class AccngPlugin(Plugin):
    def __init__(self, module):
        Plugin.__init__(self, module)
        self.name = "1secmail Mail Provider Plugin"
        self.description = "You can read and generate emails from 1secmail.com"
        self.author = ["Jeeva"]

    def run(self):
        self.module.email_server = OneSecMail()
        log.info("1secmail API loaded")
    
