#!/usr/bin/env python3
# coding=utf-8

"""
Copyright (c) 2019 mullaihub developers (https://www.mullaihub.com/accng)
See the file 'LICENSE' for copying permission
"""

import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.module import Module
from util import log
from util.colorify import green, red, bold


class AccngModule(Module):
    def __init__(self):
        super().__init__()
        self.name = "Facebook Accounts Formatter"
        self.description = "Allows you to format and remove dead Facebook IDs"
        self.author = ["Jeeva"]
        output_file = os.path.join(os.path.expanduser("~"), "Desktop", "accounts.txt")
        self.options.add("file", "", "Accounts file path")
        self.options.add("output_file", output_file, "Accounts file path")
        self.options.add("cleanup", "yes", "Remove dead IDs (yes, no)")
        self.options.add("check_cookie", "no", "Check cookies live or not (yes, no)")
        self.options.add("format", "email|pass|uid|cookie", "Account format to output (email,pass,2fa,token,cookie)")
        self.options.add("worker", "5", "How many workers to use for formatter")

    def clean_account(self, account):
        """Check if an account is live or dead."""
        url = f"https://graph.facebook.com/{account['uid']}/picture?type=normal"
        r = requests.get(url)
        if "jpg?" in r.url:
            log.info(f"Account '{green(account['uid'])}' is live")
            return account  # Account is live
        else:
            log.info(f"Account '{red(account['uid'])}' is dead")
            return None  # Account is dead
    
    def check_account(self, account):
        """Check if an account cookie is live or dead."""
        cookies = dict(item.split("=") for item in account["cookie"].split(";"))
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.152 Mobile Safari/537.36"
        })
        session.cookies.update(cookies)
        r = session.get("https://mbasic.facebook.com/?_rdc=1&_rdr")
        if "something went wrong" in r.text:
            log.info(f"Account {bold("cookie")} '{red(account['uid'])}' is dead")
            return None
        else:
            log.info(f"Account {bold("cookie")} '{green(account['uid'])}' is live")
            return account

    def run(self):
        file = self.options.get("file").strip()
        output_file = self.options.get("output_file").strip()
        cleanup = self.options.get("cleanup").strip().lower()
        check_cookie = self.options.get("check_cookie").strip().lower()
        account_format = self.options.get("format").strip().lower()
        worker = int(self.options.get("worker").strip())

        if not os.path.exists(file):
            raise Exception(f"File '{file}' does not exist")
        
        with open(file, "r") as f:
            lines = f.read().strip().split("\n")
        accounts = []
        for line in lines:
            parts = line.split("|")
            if len(parts) == 6:
                accounts.append({
                    "email": parts[0],
                    "pass": parts[1],
                    "uid": parts[2],
                    "2fa": parts[3],
                    "token": parts[4],
                    "cookie": parts[5],
                })
            if len(parts) == 4:
                accounts.append({
                    "email": parts[0],
                    "pass": parts[1],
                    "uid": parts[2],
                    "cookie": parts[3],
                })
            else:
                accounts.append({
                    "email": parts[0],
                    "pass": parts[1],
                    "uid": parts[2],
                    "2fa": "",
                    "token": parts[3],
                    "cookie": parts[4],
                })
        
        if cleanup == "yes":
            log.info("Account checking...")
            output = []
            with ThreadPoolExecutor(max_workers=worker) as executor:
                # Submit tasks to the executor
                futures = [executor.submit(self.clean_account, account) for account in accounts]
                for future in as_completed(futures):
                    account_status = future.result()
                    if account_status:  # Only add live accounts
                        output.append(account_status)
        else:
            output = accounts

        
        if check_cookie == "yes":
            log.info(f"Account {bold("cookie")} checking...")
            tmp_output = []
            with ThreadPoolExecutor(max_workers=worker) as executor:
                # Submit tasks to the executor
                futures = [executor.submit(self.check_account, account) for account in output]
                for future in as_completed(futures):
                    account_status = future.result()
                    if account_status:  # Only add live accounts
                        tmp_output.append(account_status)
            output = tmp_output

        format_parts = account_format.split("|")
        s = ""
        for o in output:
            for f in format_parts:
                if f == "email":
                    s += f"{o['email']}|"
                elif f == "pass":
                    s += f"{o['pass']}|"
                elif f == "uid":
                    s += f"{o['uid']}|"
                elif f == "2fa":
                    s += f"{o['2fa']}|"
                elif f == "token":
                    s += f"{o['token']}|"
                elif f == "cookie":
                    s += f"{o['cookie']}|"
            s = f"{s[:-1]}\n"

        with open(output_file, "w") as f:
            f.write(s)
        log.success(f"Live accounts: {bold(green(str(len(output))))}, Dead accounts: {bold(red(str(len(accounts) - len(output))))}")
        log.success(f"Accounts are written to '{output_file}'")
