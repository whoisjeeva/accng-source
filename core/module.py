#!/usr/bin/env python3
# coding=utf-8

"""
Copyright (c) 2019 mullaihub developers (https://www.mullaihub.com/accng)
See the file 'LICENSE' for copying permission
"""

import os
import types
import sys

from core.options import Options
from core.extension import EXTENSION
from core.encoder import Encoder
from util import log
from util.colorify import bold, blue, cyan
from lib.table import Table


class Module:
    def __init__(self):
        self.name = "-"
        self.description = "-"
        self.author = []
        self.license = "MIT"
        self.emoji = None

        self.options = Options()
        self.plugins = []
        self.plugin_strings = []
        self.jk = "knbjhyugs567yhbj"
        self.enc = Encoder(self.jk)

        for root, dirs, files in os.walk("plugins"):
            if "__pycache__" in root:
                continue
            root = root.replace("\\", "/")
            for f in files:
                rt = "/".join(root.split("/")[1:])
                if rt.strip():
                    path = "{}/{}".format(rt, f)
                else:
                    path = "{}".format(f)
                if path.endswith(f".{EXTENSION}"):
                    ms = ".".join(path.split(".")[:-1])
                    self.plugin_strings.append(ms)

    def setup(self):
        return True

    def do_run(self, line):
        """run the module"""
        for plugin in self.plugins:
            try:
                plugin.run()
            except Exception as e:
                log.error("A plugin failed: {}".format(e))
        if self.plugins:
            log.info("Plugins execution done")
        try:
            self.run()
        except Exception as e:
            log.error("Module failed: {}".format(e))
        log.info("Done.")

    def do_options(self, line):
        """show available options"""
        print("\nModule Options:\n")
        options = self.options.to_dict()
        if options:
            table = Table()
            values = []
            descriptions = []
            for op in options.keys():
                values.append(options[op]["value"])
                descriptions.append(options[op]["description"])

            table.add("Options", list(options.keys()))
            table.add("Default Values", values)
            table.add("Description", descriptions)

            print(table)

        print(self.description)
        print()

        if self.plugins:
            print("\nPlugin(s) Options:\n")
            for plugin in self.plugins:
                print(cyan("* {}  =>\n".format(plugin.name)))
                plugin.do_options("")

    def do_reset(self, line):
        """reset module or plugin options"""
        nodes = line.split(" ")
        try:
            if nodes[0].upper() == "PLUGIN":
                for plugin in self.plugins:
                    plugin.options.reset(nodes[1])
                log.info("{} => {}".format(nodes[1], self.options.get(nodes[1])))
            else:
                self.options.reset(nodes[0])
                log.info("{} => {}".format(nodes[0], self.options.get(nodes[0])))
        except IndexError:
            log.error("Insufficient arguments")
    
    def complete_reset(self, text, line, begidx, endidx):
        options = self.options.to_dict()

        nodes = line.split(" ")
        mline = self.autocomp(line, len(nodes) - 1)
        offs = len(mline) - len(text)
        comps = []
        if len(nodes) <= 2:
            comps = list(options.keys())
            if self.plugins:
                comps += ["PLUGIN"]
            if text.isupper():
                comps = [s.upper() for s in comps]
            else:
                comps = [s.lower() for s in comps]
        elif len(nodes) <= 3:
            node = line.split(" ")[1]
            if node.upper() == "PLUGIN":
                comps = []
                for plugin in self.plugins:
                    comps += list(plugin.options.to_dict().keys())
                if text.isupper():
                    comps = [s.upper() for s in comps]
                else:
                    comps = [s.lower() for s in comps]
        elif len(nodes) <= 4:
            pass

        return [s[offs:] for s in comps if s.startswith(mline)]

    def do_set(self, line):
        """set module or plugin options"""
        nodes = line.split(" ")
        try:
            if nodes[0].upper() == "PLUGIN":
                nodes.pop(0)
                key = nodes.pop(0)
                value = " ".join(nodes)
                for plugin in self.plugins:
                    plugin.options.set(key, value)
                log.info("{} => {}".format(key, value))
            else:
                key = nodes.pop(0)
                value = " ".join(nodes)
                self.options.set(key, value)
                log.info("{} => {}".format(key, value))
        except IndexError:
            log.error("Insufficient arguments")

    def complete_set(self, text, line, begidx, endidx):
        options = self.options.to_dict()

        nodes = line.split(" ")
        mline = self.autocomp(line, len(nodes) - 1)
        offs = len(mline) - len(text)
        comps = []
        if len(nodes) <= 2:
            comps = list(options.keys())
            if self.plugins:
                comps += ["PLUGIN"]
            if text.isupper():
                comps = [s.upper() for s in comps]
            else:
                comps = [s.lower() for s in comps]
        elif len(nodes) <= 3:
            node = line.split(" ")[1]
            if node.upper() == "PLUGIN":
                comps = []
                for plugin in self.plugins:
                    comps += list(plugin.options.to_dict().keys())
                if text.isupper():
                    comps = [s.upper() for s in comps]
                else:
                    comps = [s.lower() for s in comps]
        elif len(nodes) <= 4:
            pass

        return [s[offs:] for s in comps if s.startswith(mline)]

    def autocomp(self, line, num):
        mline = line.partition(" ")[2]
        for i in range(num - 1):
            mline = mline.partition(" ")[2]

        return mline

    def do_unload(self, line):
        """unload or remove a loaded plugin"""
        try:
            if EXTENSION == "py" or EXTENSION == "pyc":
                plug = __import__("plugins.{}".format(line.replace("/", ".")), fromlist=["AccngPlugin"]).AccngPlugin(self)
            else:
                with open(f"plugins/{line}.m", "r") as f:
                    code = f.read()
                decrypted_code = self.enc.d(code)
                module_name = "dynamic_module"
                dynamic_module = types.ModuleType(module_name)
                sys.modules[module_name] = dynamic_module
                exec(decrypted_code, dynamic_module.__dict__)
                plug = dynamic_module.AccngPlugin(self)
            
            index = -1
            for i, p in enumerate(self.plugins):
                if p.name == plug.name:
                    index = i
                    break
            if index > -1:
                self.plugins.pop(index)
            else:
                log.error("Plugin '{}' not loaded".format(line))
        except (AttributeError, FileNotFoundError):
            log.error("Unknown Accng plugin")
    
    def complete_unload(self, text, line, begidx, endidx):
        nodes = line.split(" ")
        mline = self.autocomp(line, len(nodes) - 1)
        offs = len(mline) - len(text)
        comps = []
        if len(nodes) <= 2:
            comps = self.plugin_strings
        return [s[offs:] for s in comps if s.startswith(mline)]

    def do_load(self, line):
        """load a plugin into a module"""
        try:
            if EXTENSION == "py" or EXTENSION == "pyc":
                plug = __import__("plugins.{}".format(line.replace("/", ".")), fromlist=["AccngPlugin"]).AccngPlugin(self)
            else:
                with open(f"plugins/{line}.m", "r") as f:
                    code = f.read()
                decrypted_code = self.enc.d(code)
                module_name = "dynamic_module"
                dynamic_module = types.ModuleType(module_name)
                sys.modules[module_name] = dynamic_module
                exec(decrypted_code, dynamic_module.__dict__)
                plug = dynamic_module.AccngPlugin(self)
            if plug.setup():
                self.plugins.append(plug)
            else:
                log.error("Unable to load '{}' setup failed".format(line))
        except (AttributeError, FileNotFoundError):
            log.error("Unknown Accng plugin")

    def complete_load(self, text, line, begidx, endidx):
        nodes = line.split(" ")
        mline = self.autocomp(line, len(nodes) - 1)
        offs = len(mline) - len(text)
        comps = []
        if len(nodes) <= 2:
            comps = self.plugin_strings
        return [s[offs:] for s in comps if s.startswith(mline)]

    def log_info(self, s):
        log.info(s)

    def log_error(self, s):
        log.error(s)

    def log_warn(self, s):
        log.warn(s)

    def log_success(self, s):
        log.success(s)


class Plugin:
    def __init__(self, module):
        self.name = "-"
        self.description = "-"
        self.author = []
        self.license = "MIT"

        self.module = module
        self.options = Options()

    def setup(self):
        return True

    def run(self):
        pass

    def do_options(self, line):
        options = self.options.to_dict()
        if options:
            table = Table()
            values = []
            descriptions = []
            for op in options.keys():
                values.append(options[op]["value"])
                descriptions.append(options[op]["description"])

            table.add("Options", list(options.keys()))
            table.add("Default Values", values)
            table.add("Description", descriptions)

            print(table)
        print(self.description)
        print()

    def log_info(self, s):
        log.info(s)

    def log_error(self, s):
        log.error(s)

    def log_warn(self, s):
        log.warn(s)

    def log_success(self, s):
        log.success(s)