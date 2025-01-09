#!/usr/bin/env python3
# coding=utf-8

"""
Copyright (c) 2019 mullaihub developers (https://www.mullaihub.com/accng)
See the file 'LICENSE' for copying permission
"""


def bold(s):
    return "\001\033[1m\002{}\001\033[0m\002".format(s)


def dim(s):
    return "\001\033[2m\002{}\001\033[0m\002".format(s)


def underline(s):
    return "\001\033[4m\002{}\001\033[0m\002".format(s)


def inverted(s):
    return "\001\033[7m\002{}\001\033[0m\002".format(s)


def black(s):
    return "\001\033[30m\002{}\001\033[0m\002".format(s)


def red(s):
    return "\001\033[31m\002{}\001\033[0m\002".format(s)


def green(s):
    return "\001\033[32m\002{}\001\033[0m\002".format(s)


def yellow(s):
    return "\001\033[33m\002{}\001\033[0m\002".format(s)


def blue(s):
    return "\001\033[34m\002{}\001\033[0m\002".format(s)


def magenta(s):
    return "\001\033[35m\002{}\001\033[0m\002".format(s)


def cyan(s):
    return "\001\033[36m\002{}\001\033[0m\002".format(s)


def light_gray(s):
    return "\001\033[37m\002{}\001\033[0m\002".format(s)


def gray(s):
    return "\001\033[90m\002{}\001\033[0m\002".format(s)


def light_red(s):
    return "\001\033[91m\002{}\001\033[0m\002".format(s)


def light_green(s):
    return "\001\033[92m\002{}\001\033[0m\002".format(s)


def light_yellow(s):
    return "\001\033[93m\002{}\001\033[0m\002".format(s)


def light_blue(s):
    return "\001\033[94m\002{}\001\033[0m\002".format(s)


def light_magenta(s):
    return "\001\033[95m\002{}\001\033[0m\002".format(s)


def light_cyan(s):
    return "\001\033[96m\002{}\001\033[0m\002".format(s)


def white(s):
    return "\001\033[97m\002{}\001\033[0m\002".format(s)


def red_bg(s):
    return "\001\033[41m\002{}\001\033[0m\002".format(s)


def green_bg(s):
    return "\001\033[42m\002{}\001\033[0m\002".format(s)


def yellow_bg(s):
    return "\001\033[43m\002{}\001\033[0m\002".format(s)


def blue_bg(s):
    return "\001\033[44m\002{}\001\033[0m\002".format(s)


def magenta_bg(s):
    return "\001\033[45m\002{}\001\033[0m\002".format(s)


def cyan_bg(s):
    return "\001\033[46m\002{}\001\033[0m\002".format(s)


def light_gray_bg(s):
    return "\001\033[47m\002{}\001\033[0m\002".format(s)


def light_red_bg(s):
    return "\001\033[101m\002{}\001\033[0m\002".format(s)


def light_green_bg(s):
    return "\001\033[102m\002{}\001\033[0m\002".format(s)


def light_yellow_bg(s):
    return "\001\033[103m\002{}\001\033[0m\002".format(s)


def light_blue_bg(s):
    return "\001\033[104m\002{}\001\033[0m\002".format(s)


def light_magenta_bg(s):
    return "\001\033[105m\002{}\001\033[0m\002".format(s)


def light_cyan_bg(s):
    return "\001\033[106m\002{}\001\033[0m\002".format(s)


def white_bg(s):
    return "\001\033[107m\002{}\001\033[0m\002".format(s)