#!/usr/bin/env python3
# coding=utf-8

"""
Copyright (c) 2019 mullaihub developers (https://www.mullaihub.com/accng)
See the file 'LICENSE' for copying permission
"""

import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import time

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
        self.options.add("format", "email|username|pass|2fa", "Account format to output (email,pass,username,2fa,cookie)")
        self.options.add("worker", "5", "How many workers to use for formatter")

    def extract_username(self, text):
        pattern = r'"username"\:"[a-z0-9]+"'
        match = re.search(pattern, text)

        if match:
            return match.group().split('":"')[-1][:-1]
        else:
            return None

    def clean_account(self, account):
        """Check if an account is live or dead."""
        try:
            url = f"https://www.famety.com/phpCurl"  # API endpoint for user info
            r = requests.post(url, data={
                "user": account["username"],
                "socialMedia": "",
                "productAsks": '{"sm_domain":"https://www.instagram.com/","preview":"1","sm_type_id":"usernameChecker","sm_id":"1","link_status":0,"image_way":"","pid":3,"page_id":17781}',
                "multiOptionTake": "",
                "nextTimeline": "",
                "forGenerator": "true"
            }, headers = {
                "x-requested-with": "XMLHttpRequest",
                "referer": "https://www.famety.com/instagram-username-checker",
            })
            status = r.json()["status"]
            if status == "success":
                log.info(f"Account '{green(account['username'])}' ({bold(self.extract_username(r.text))}) is live")
                return account
            else:
                log.info(f"Account '{red(account['username'])}' is dead")
                return None  # Account is dead
        except:
            log.warn("Network error retrying...")
            time.sleep(2)
            return self.clean_account(account)

    def cookie_parser(self, cookie):
        nodes = cookie.split(";")
        output = []
        for node in nodes:
            parts = node.split("=")
            name = parts.pop(0)
            value = "=".join(parts)
            output.append({ "name": name, "value": value })
        return output

    def run(self):
        file = self.options.get("file").strip()
        output_file = self.options.get("output_file").strip()
        cleanup = self.options.get("cleanup").strip().lower()
        account_format = self.options.get("format").strip().lower()
        worker = int(self.options.get("worker").strip())

        if not os.path.exists(file):
            raise Exception(f"File '{file}' does not exist")
        
        with open(file, "r") as f:
            lines = f.read().strip().split("\n")
        accounts = []
        for line in lines:
            parts = line.split("|")
            if len(parts) == 3:
                cookies = self.cookie_parser(parts[2])
            else:
                cookies = self.cookie_parser(parts[3])
            uid = None
            for c in cookies:
                if c["name"] == "ds_user_id" or c["name"] == "ig-u-ds-user-id":
                    uid = c["value"]
                    break

            if len(parts) == 3:
                accounts.append({
                    "email": parts[0],
                    "username": "",
                    "pass": parts[1],
                    "uid": uid,
                    "cookie": parts[2],
                })
            else:
                accounts.append({
                    "email": parts[0],
                    "username": parts[1],
                    "pass": parts[2],
                    "uid": uid,
                    "2fa": parts[3],
                    "cookie": parts[4] if len(parts) >= 5 else "",
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


        format_parts = account_format.split("|")
        s = ""
        for o in output:
            for f in format_parts:
                if f == "email":
                    s += f"{o['email']}|"
                elif f == "username":
                    s += f"{o['username']}|"
                elif f == "pass":
                    s += f"{o['pass']}|"
                elif f == "uid":
                    s += f"{o['uid']}|"
                elif f == "2fa":
                    s += f"{o['2fa']}|"
                elif f == "cookie":
                    s += f"{o['cookie']}|"
            s = f"{s[:-1]}\n"

        with open(output_file, "w") as f:
            f.write(s)
        log.success(f"Live accounts: {bold(green(str(len(output))))}, Dead accounts: {bold(red(str(len(accounts) - len(output))))}")
        log.success(f"Accounts are written to '{output_file}'")
