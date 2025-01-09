#!/usr/bin/env python3
# coding=utf-8

"""
Copyright (c) 2019 mullaihub developers (https://www.mullaihub.com/accng)
See the file 'LICENSE' for copying permission
"""

from core.module import Plugin
from core.mail import TenMinuteMail
from util import log


class AccngPlugin(Plugin):
    def __init__(self, module):
        Plugin.__init__(self, module)
        self.name = "10minutemail Mail Provider Plugin"
        self.description = "You can read and generate emails from 10minutemail.net"
        self.author = ["Jeeva"]

    def run(self):
        self.module.email_server = TenMinuteMail()
        log.info("10minutemail API loaded")
