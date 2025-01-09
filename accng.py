#!/usr/bin/env python3
# coding=utf-8

"""
Copyright (c) 2019 mullaihub developers (https://www.mullaihub.com/accng)
See the file 'LICENSE' for copying permission
"""

import os
import base64
import requests
import os
import types
import sys
import uuid

from core.extension import EXTENSION
from core.console import Console
from core.encoder import Encoder
from lib.argparse import ArgParse
from util import log
from util.colorify import red, green, underline, yellow
from util import banner


class Accng(Console):
    def __init__(self):
        Console.__init__(self)
        self.jk = "knbjhyugs567yhbj"
        self.parser = self.parse_arguments()
        self.args = self.parser.parse()
        self.module = {
            "name": None,
            "commands": [],
            "instance": None
        }
        self.modules_string = []
        self.enc = Encoder(self.jk)
        id_path = os.path.join(os.path.expanduser('~'), ".accng_id")
        if not os.path.exists(id_path):
            with open(id_path, "w") as f:
                f.write(uuid.uuid4().hex) 

        for root, dirs, files in os.walk("modules"):
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
                    self.modules_string.append(ms)

        banner.print_banner()
        if self.args.use:
            self.do_use(self.args.use)

    def parse_arguments(self):
        parser = ArgParse(argument_space_count=20, usage="accng [options]")
        parser.add_argument(["--help", "-h"], description="show help", is_flag=True)
        parser.add_argument(["--use", "-u"], example="payload", description="use a specific module")
        return parser

    def route(self):
        if self.args.help:
            self.parser.print_help()
            return

        try:
            self.cmdloop()
        except KeyboardInterrupt:
            self.postloop()

    def do_use(self, line):
        """load a module to use"""
        try:
            if EXTENSION == "py" or EXTENSION == "pyc":
                mod = __import__("modules." + line.strip().replace("/", "."), fromlist=["AccngModule"]).AccngModule()
            else:
                with open(f"modules/{line}.m", "r") as f:
                    code = f.read()
                decrypted_code = self.enc.d(code)
                module_name = "dynamic_module"
                dynamic_module = types.ModuleType(module_name)
                sys.modules[module_name] = dynamic_module
                exec(decrypted_code, dynamic_module.__dict__)
                mod = dynamic_module.AccngModule()
            can_load = mod.setup()
            if can_load:
                self.module["instance"] = mod
                self.module["name"] = line.strip()
                self.module["commands"].clear()
                for cmd in dir(mod):
                    if cmd.startswith("do_"):
                        self.module["commands"].append(cmd)
                    elif cmd.startswith("complete_"):
                        setattr(self, cmd, getattr(mod, cmd))
                self.update_prompt(mod.emoji)
            else:
                log.error("Unable to load '{}' setup failed".format(line))
        except (ModuleNotFoundError, ValueError) as e:
            log.error("Module Exception: {}".format(e))
        except AttributeError:
            log.error("Unknown Accng module")

    def update_prompt(self, emoji):
        em = ""
        if emoji is not None:
            em = emoji
        if self.module["name"] is not None:
            nodes = self.module["name"].split("/")
            if len(nodes) == 1:
                self.prompt = "{} {} {}({}) → ".format(underline(green("accng")), red(nodes[0]), yellow(nodes[-1]))
            else:
                head_node = nodes.pop(0)
                self.prompt = f"{underline(green("accng"))} {em}{red(head_node)}({yellow("_".join(nodes))}) → "
        else:
            self.prompt = "{} → ".format(underline(green("accng")))

    def completenames(self, text, *ignored):
        dotext = "do_" + text
        return [a[3:] for a in self.get_names() + self.module["commands"] if a.startswith(dotext)]

    def complete_use(self, text, line, begidx, endidx):
        mline = line.partition(" ")[2]
        offs = len(mline) - len(text)
        return [s[offs:] for s in self.modules_string if s.startswith(mline)]

    def default(self, line):
        nodes = line.split(" ")
        if "do_" + nodes[0].strip() in self.module["commands"] and self.module["instance"] is not None:
            getattr(self.module["instance"], "do_" + nodes[0].strip())(" ".join(nodes[1:]).strip())
        else:
            log.info("Exec: {}\n".format(line))
            os.system(line)

    def do_help(self, line):
        """show available commands use cases"""
        print("\nCore Commands:\n")
        meths = dir(self)
        for meth in meths:
            if meth.startswith("do_"):
                s = meth.replace("do_", "")
                doc = getattr(self, meth).__doc__
                if doc is None:
                    doc = "-"
                print("{}{}: {}".format(s, " " * (10 - len(s)), doc))
        print()

        if self.module["instance"] is not None:
            print("Module Commands:\n")
            for meth in self.module["commands"]:
                s = meth.replace("do_", "")
                doc = getattr(self.module["instance"], meth).__doc__
                if doc is None:
                    doc = "-"
                print("{}{}: {}".format(s, " " * (10 - len(s)), doc))
            print()


if __name__ == "__main__":
    accng = Accng()
    accng.route()