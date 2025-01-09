#!/usr/bin/env python3
# coding=utf-8

"""
Copyright (c) 2019 mullaihub developers (https://www.mullaihub.com/accng)
See the file 'LICENSE' for copying permission
"""

from telethon.sync import TelegramClient
import json

from core.module import Module
from util import log
from util.colorify import bold, underline


class AccngModule(Module):
    def __init__(self):
        Module.__init__(self)
        self.name = "Telegram Session File Generator"
        self.description = f"Generate a session file for your telegram account. Get app_id and api_hash from {bold(underline("https://core.telegram.org/api/obtaining_api_id"))}"
        self.author = ["Jeeva"]
        self.options.add("app_id", "", "Telegram app ID")
        self.options.add("api_hash", "", "Telegram app API hash")

    def run(self):
        app_id = self.options.get("app_id")
        api_hash = self.options.get("api_hash")
        with TelegramClient("telegram_session.session", app_id, api_hash) as client:
            session_data = {
                'api_id': app_id,
                'api_hash': api_hash,
                'auth_key': client.session.auth_key.key.hex(),
                'dc_id': client.session.dc_id,
                'server_address': client.session.server_address,
                'port': client.session.port
            }
            with open("api.json", "w") as f:
                f.write(json.dumps(session_data))
            log.success("API JSON file generated!")
            log.success(f"Your session file is generated '{bold("telegram_session.session")}', copy the file before it get overwritten")
