#!/usr/bin/env python3
# coding=utf-8

"""
Copyright (c) 2019 mullaihub developers (https://www.mullaihub.com/accng)
See the file 'LICENSE' for copying permission
"""


class Options:
    def __init__(self):
        self._options = {}
        self.defaults = {}

    def __repr__(self):
        return str(self._options)

    def add(self, key, value, description=""):
        self.defaults[key.upper()] = {
            "value": value,
            "description": description
        }
        self._options[key.upper()] = {
            "value": value,
            "description": description
        }

    def get(self, key):
        return self._options[key.upper()]["value"]

    def set(self, key, value):
        if key.upper() in self._options:
            self._options[key.upper()]["value"] = value

    def reset(self, key):
        if key.upper() in self.defaults:
            self._options[key.upper()]["value"] = self.defaults[key.upper()]["value"]

    def to_dict(self):
        return self._options