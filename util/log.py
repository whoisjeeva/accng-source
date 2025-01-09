#!/usr/bin/env python3
# coding=utf-8

"""
Copyright (c) 2019 mullaihub developers (https://www.mullaihub.com/accng)
See the file 'LICENSE' for copying permission
"""

import sys

from util.formatter import format_percentage
from util.system import is_win, terminal_width, get_time
from util.colorify import blue, red, green, yellow, green_bg, black, bold


def info(s):
    print("[{}] {}".format(bold(blue(" INFO ")), s))


def warn(s):
    print("[{}] {}".format(bold(yellow(" WARN ")), yellow(s)))


def error(s):
    print("[{}] {}".format(bold(red(" FAIL ")), red(s)))


def success(s):
    print("[{}] {}".format(bold(green("  OK  ")), s))