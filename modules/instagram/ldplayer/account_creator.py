#!/usr/bin/env python3
# coding=utf-8

"""
Copyright (c) 2019 mullaihub developers (https://www.mullaihub.com/accng)
See the file 'LICENSE' for copying permission
"""

from bs4 import BeautifulSoup
import re
import subprocess
import time
import os
import sys
import random
import requests
import json
from urllib3.exceptions import ProtocolError, IncompleteRead
from requests.exceptions import ChunkedEncodingError
import base64
import pyotp
import survey
from pathlib import Path
import win32gui
import win32con
import glob
from slugify import slugify
import uuid
import hashlib
import hmac
import threading
import tempfile

from core.module import Module
from util.name_generator import random_name, names
from util.phone_number import generate_phone_number
from util import log
from util.system import terminal_width
from data.device import devices
from util.colorify import bold, yellow, red, yellow_bg, black, green_bg, light_gray_bg


class AccngModule(Module):
    def __init__(self):
        Module.__init__(self)
        self.name = "Instagram Account Creator"
        self.description = "Create Instagram accounts (AutoReg)"
        self.author = ["Jeeva"]
        self.options.add("country", "bangladesh", "For names & phone number (cmd: countries)")
        self.options.add("password", "Mullai123@", "Password for account creation")
        self.options.add("2fa", "no", "Enable 2FA after creating account (yes, no)")
        self.options.add("emulator_count", "1", "How many emulators to use")
        self.options.add("account_count", "1", "How many accounts to create with each emulator")
        self.options.add("headless", "no", "Hide emulators while creating accounts (yes, no)")
        self.options.add("wait_time", "15", "Default wait time in seconds")

        self.home_dir = os.path.abspath("C:\\")  # Get the user's home directory
        self.ldplayer_dir = os.path.join(self.home_dir, "ldplayer")
        self.dnconsole = os.path.join(self.ldplayer_dir, "dnconsole.exe")
        self.adb = os.path.join(self.ldplayer_dir, "adb.exe")
        self.window_names = []

        self.options.add("ldplayer", self.ldplayer_dir, "LDPlayer path")

        self.options.add("proxy_file", "", "Use a Socks5 proxy file each proxy on newline")
        self.options.add("proxy_selection", "2", "1 for random 2 for one by one")
        self.options.add("manufacturer_model", "random", "Device manufacturer & model (random)")
        self.options.add("imei", "random", "IMEI number")
        self.options.add("imsi", "random", "IMSI number")
        self.options.add("sim_serial", "random", "SIM serial number")
        self.options.add("android_id", "random", "Android device ID")
        self.options.add("mac", "random", "MAC address")
        self.options.add("change_ad_id", "no", "Change Google AD ID (yes, no)")
        self.options.add("language", "en-US", "Device language")
        self.public_ip = "Unknown"
        try:
            r = requests.get("https://ipinfo.io/json").json()
            self.public_ip = r["ip"]
            self.options.add("timezone", r["timezone"], "Timezone for emulator")
        except:
            self.options.add("timezone", "Unknown", "Timezone for emulator")
        
        self.description = f"Using LDPlayer to create Instagram account, {bold(yellow("required a mail server plugin."))} Public IP: {bold(red(self.public_ip))}"

    def run(self):
        log.success("Done.")

    def do_countries(self, line):
        """list supported countries"""
        for k in names.keys():
            log.info(k)
    
    def run_runner(self, adb_id, proxy, account_count, emu_names):
        try:
            runner = Runner(
                adb=self.adb,
                adb_id=adb_id,
                password=self.options.get("password").strip(),
                is_twofa=self.options.get("2fa").strip().lower() == "yes",
                change_ad_id=self.options.get("change_ad_id").strip().lower(),
                country=self.options.get("country").strip().lower(),
                proxy=proxy,
                email_server=self.email_server,
                wait_time=self.wait_time,
                stop_event=self.stop_event,
                account_count=account_count,
                emu_names=emu_names,
                dnconsole=self.dnconsole
            )
            runner.start()
        except KeyboardInterrupt:
            self.stop_event.set()
        except:
            pass

    def run(self):
        self.ldplayer_dir = self.options.get("ldplayer")
        self.dnconsole = os.path.join(self.ldplayer_dir, "dnconsole.exe")
        self.adb = os.path.join(self.ldplayer_dir, "adb.exe")

        self.stop_event = threading.Event()
        if not os.path.exists(self.dnconsole):
            log.warn(f"LDPlayer does not exist, set the LDPlayer path or download from {bold("https://1drv.ms/u/s!AhrEKQyGOJTXchpWn-admIIK1Ss?e=EUWpOP")} and extract it to C drive.")
            return

        ds = base64.b64decode("amsgPSBzdXJ2ZXkucm91dGluZXMuaW5wdXQoYmFzZTY0LmI2NGRlY29kZSgiUVdOalpYTnpJRXRsZVQ4ZyIpLmRlY29kZSgidXRmLTgiKSk=").decode('utf-8')
        local_vars = {}
        exec(ds, globals(), local_vars)
        id_path = os.path.join(os.path.expanduser('~'), ".accng_id")
        device_id = ""
        if os.path.exists(id_path):
            with open(id_path, "r") as f:
                device_id = f.read().strip()
        r = requests.get(f"https://www.urdunub.com/fbcreate/check_key/{local_vars["jk"]}?device_id={device_id}").json()
        if r["status"] != "valid":
            log.error(r["message"])
            return

        files_to_remove = glob.glob("profile*.jpg")
        for file_path in files_to_remove:
            if os.path.exists(file_path):
                os.remove(file_path)
        if not hasattr(self, "email_server"):
            log.error("No mail server is loaded, please load a mail server before running.")
            return

        self.wait_time = int(self.options.get("wait_time"))
        # proxy = self.options.get("proxy").strip()
        # if proxy != "":
        #     is_proxy_working = self.check_proxy(proxy)
        #     if not is_proxy_working:
        #         return
        self.window_names.clear()
        emulator_count = int(self.options.get("emulator_count"))
        proxy_file = self.options.get("proxy_file")
        proxy_selection = self.options.get("proxy_selection")
        account_count = int(self.options.get("account_count"))

        proxies = []
        if proxy_file.strip() != "":
            log.info("Checking your proxy list...")
            with open(proxy_file, "r") as f:
                tmp = f.read().strip().split("\n")
            for t in tmp:
                is_proxy_working = self.check_proxy(t)
                if is_proxy_working:
                    proxies.append(t)
        
        proxy_index = 0
        log.info("Killing ADB services...")
        subprocess.run(["taskkill", "/F", "/IM", "adb.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        threads = []
        try:
            while not self.stop_event.is_set():
                emu_names = []
                for i in range(emulator_count):
                    emu_names.append(f"accng{i}")
                    self.launch_emulator(f"accng{i}")
                self.handle_headless()
                adb_ids = self.find_adb_devices(emulator_count)
                if len(adb_ids) == 0:
                    continue

                log.info(f"ADB connection found: {adb_ids}")
                proxy = None
                if len(proxies) > 0:
                    if proxy_selection == "2":
                        proxy = random.choice(proxies)
                    else:
                        if proxy_index >= len(proxies):
                            proxy_index = 0
                        proxy = proxies[proxy_index]
                        proxy_index += 1

                for adb_id in adb_ids:
                    thread = threading.Thread(target=self.run_runner, args=(adb_id, proxy, account_count, emu_names), daemon=True)
                    threads.append(thread)
                    thread.start()

                while any(thread.is_alive() for thread in threads):
                    time.sleep(1)

        except KeyboardInterrupt:
            self.stop_event.set()
            log.info("Ctrl+C detected, terminating threads...")

    def set_hardware_fingerprint(self, emulator_name):
        log.info("Changing fingerprint...")
        manufacturer_model = self.options.get("manufacturer_model").strip()
        imei = self.options.get("imei").strip()
        imsi = self.options.get("imsi").strip()
        sim_serial = self.options.get("sim_serial").strip()
        android_id = self.options.get("android_id").strip()
        mac = self.options.get("mac").strip()

        if imei == "random":
            imei = "auto"
        if imsi == "random":
            imsi = "auto"
        if sim_serial == "random":
            sim_serial = "auto"
        if android_id == "random":
            android_id = uuid.uuid4().hex
        if manufacturer_model == "random":
            d = random.choice(devices)
            manufacturer_model = f"{d["manufacturer"]},{d["model"]}"
        if mac == "random":
            mac = "auto"
        
        mans = manufacturer_model.split(",")
        manufacturer = mans.pop(0)
        model = ",".join(mans)
        log.info(f"Manufacturer: {manufacturer}, Model: {model}")
        subprocess.run([self.dnconsole, "modify", "--name", emulator_name, "--imei", imei, "--imsi", imsi, "--simserial", sim_serial, "--androidid", android_id, "--mac", mac, "--manufacturer", manufacturer, "--model", model], capture_output=True, text=True)

    def execute_command(self, command):
        # Start the process
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)

        # Read output in real-time
        output = ""
        for line in iter(process.stdout.readline, ''):
            output += line

        # Wait for the process to complete and return the final output
        process.stdout.close()
        process.wait()

        return output

    def get_online_adb_devices(self):
        result = self.execute_command(f"{self.adb} devices")
        lines = result.splitlines()
        online_devices = []

        for line in lines[1:]:
            if '\tdevice' in line:  # We are only interested in lines that contain '\tdevice'
                device_id = line.split('\t')[0]  # Extract the device ID
                online_devices.append(device_id)

            if "offline" in line:
                subprocess.run([self.adb, "kill-server"], capture_output=True, text=True, timeout=5)

        return online_devices

    def find_adb_devices(self, emulator_count):
        log.info("Looking for ADB connection...")
        count = 0
        adb_devices = []
        while True:
            if count >= (self.wait_time*2):
                count = 0
                # subprocess.run(f"{self.adb} kill-server", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                break
            adb_devices = self.get_online_adb_devices()
            if len(adb_devices) >= emulator_count:
                break
            time.sleep(1)
            count += 1
        return adb_devices

    def move_window(window_title, x, y):
        # Find the window handle based on the title
        hwnd = win32gui.FindWindow(None, window_title)
        if hwnd:  # Check if the window was found
            # Get the current window size and position
            rect = win32gui.GetWindowRect(hwnd)
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]
            
            # Move the window to the specified (x, y) position
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, x, y, width, height, win32con.SWP_NOZORDER)
        else:
            print("Window not found!")

    def handle_headless(self):
        headless = self.options.get("headless").strip().lower()
        log.info(f"Headless mode: {bold(headless.title())}")
        if headless == "yes":
            while True:
                is_found = False
                titles = self.get_all_window_titles()
                for title in titles:
                    found_names = []
                    for n in self.window_names:
                        if n == title:
                            found_names.append(title)
                    if len(found_names) == len(self.window_names):
                        is_found = True
                        break
                if is_found:
                    break
                time.sleep(0.05)

            for n in self.window_names:
                hwnd = win32gui.FindWindow(None, n)
                win32gui.ShowWindow(hwnd, 0)

    def enum_windows_callback(self, hwnd, window_titles):
        if win32gui.IsWindowVisible(hwnd):
            window_title = win32gui.GetWindowText(hwnd)
            if window_title:  # Only list windows with a title
                window_titles.append(window_title)

    def get_all_window_titles(self):
        window_titles = []
        win32gui.EnumWindows(self.enum_windows_callback, window_titles)
        return window_titles

    def wait_for_emulator_to_stop(self, emulator_name):
        while True:
            is_running = subprocess.run([self.dnconsole, "isrunning", "--name", emulator_name], capture_output=True, text=True)
            if str(is_running.stdout).strip() == "stop":
                break
            time.sleep(1)

    def wait_for_emulator_to_remove(self, emulator_name):
        while True:
            output = subprocess.run([self.dnconsole, "list"], capture_output=True, text=True)
            if emulator_name not in str(output.stdout):
                break
            time.sleep(1)

    def launch_emulator(self, emulator_name):
        log.info(f"Launching emulator {bold(emulator_name)}...")
        subprocess.run([self.dnconsole, "quit", "--name", emulator_name], capture_output=True, text=True)
        self.wait_for_emulator_to_stop(emulator_name)
        subprocess.run(f"{self.adb} kill-server", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(f"{self.adb} start-server", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run([self.dnconsole, "remove", "--name", emulator_name], capture_output=True, text=True)
        self.wait_for_emulator_to_remove(emulator_name)
        subprocess.run([self.dnconsole, "copy", "--name", emulator_name, "--from", "default"], capture_output=True, text=True)
        time.sleep(1)
        self.set_hardware_fingerprint(emulator_name)
        subprocess.run([self.dnconsole, "launch", "--name", emulator_name], capture_output=True, text=True)
        log.info("Restarting ADB...")

        self.window_names.append(emulator_name)

    def check_proxy(self, proxy):
        url = "http://httpbin.org/ip" 
        proxies = {
            "http": f"socks5://{proxy}",
            "https": f"socks5://{proxy}"
        }
        try:
            response = requests.get(url, proxies=proxies, timeout=10)
            if response.status_code == 200:
                log.info(f"Proxy {proxy} is working. IP used: {response.json()['origin']}")
                return True
            else:
                log.info(f"Proxy {proxy} returned status code {response.status_code}.")
                return False
        except requests.exceptions.RequestException as e:
            log.info(f"Proxy {proxy} is not working. Error: {e}")
            return False
 


class Runner:
    def __init__(self, adb, adb_id, password, is_twofa, change_ad_id, country, proxy, email_server, wait_time, stop_event, account_count, emu_names, dnconsole):
        self.adb = adb
        self.adb_id = adb_id
        self.password = password
        self.is_twofa = is_twofa
        self.change_ad_id = change_ad_id
        self.country = country
        self.proxy = proxy
        self.email_server = email_server
        self.wait_time = wait_time
        self.stop_event = stop_event
        self.account_count = account_count
        self.emu_names = emu_names
        self.dnconsole = dnconsole

    def set_proxy(self, proxy):
        if self.stop_event.is_set():
            raise Exception("KeyboardInterrupt!")
        if proxy.strip() != "":
            log.info(f"Setting proxy: {proxy}")
            if "@" in proxy:
                nodes = proxy.split("@")
                parts = nodes[0].split(":")
                username = parts[0]
                password = parts[1]
                parts = nodes[1].split(":")
                host = parts[0]
                port = parts[1]
            else:
                parts = proxy.split(":")
                host = parts[0]
                port = parts[1]
                username = ""
                password = ""
            subprocess.run([self.adb, "-s", self.adb_id, "shell", "monkey", "-p", "net.typeblog.socks", "-c", "android.intent.category.LAUNCHER", "1"], capture_output=True, text=True)

            layout = self.wait_for_text("Server IP")
            coords = self.get_bounds(layout, "node", {'text': 'Server IP'})
            self.click(coords)

            layout = self.wait_for_text("android:id/edit")
            coords = self.get_bounds(layout, "node", {'resource-id': 'android:id/edit'})
            self.click(coords)
            for _ in range(15):
                subprocess.run([self.adb, "-s", self.adb_id, "shell", "input", "keyevent", "67"], capture_output=True, text=True)
            self.type_text(host)

            coords = self.get_bounds(layout, "node", {'text': 'OK'})
            self.click(coords)
            time.sleep(2)
            layout = self.wait_for_text("Server Port")
            coords = self.get_bounds(layout, "node", {'text': 'Server Port'})
            self.click(coords)
            layout = self.wait_for_text("android:id/edit")
            coords = self.get_bounds(layout, "node", {'resource-id': 'android:id/edit'})
            self.click(coords)
            for _ in range(5):
                subprocess.run([self.adb, "-s", self.adb_id, "shell", "input", "keyevent", "67"], capture_output=True, text=True)
            self.type_text(port)

            coords = self.get_bounds(layout, "node", {'text': 'OK'})
            self.click(coords)

            if username != "" and password != "":
                width, height = self.get_screen_size()
                subprocess.run([self.adb, "-s", self.adb_id, "shell", "input", "swipe", "10", f"{height-10}", "10", f"{int(height/2)}"], capture_output=True, text=True)

                coords = self.get_bounds(layout, "node", {'text': 'Username & Password Authentication'})
                self.click(coords)

                coords = self.get_bounds(layout, "node", {'text': 'Username'})
                self.click(coords)

                layout = self.wait_for_text("OK")
                coords = self.get_bounds(layout, "node", {'resource-id': 'android:id/edit'})
                self.click(coords)
                self.type_text(username)
                coords = self.get_bounds(layout, "node", {'text': 'OK'})
                self.click(coords)

                layout = self.wait_for_text("Password")
                coords = self.get_bounds(layout, "node", {'text': 'Password'})
                self.click(coords)

                layout = self.wait_for_text("OK")
                coords = self.get_bounds(layout, "node", {'resource-id': 'android:id/edit'})
                self.click(coords)
                self.type_text(password)
                coords = self.get_bounds(layout, "node", {'text': 'OK'})
                self.click(coords)
            
            coords = self.get_bounds(layout, "node", {'class': 'android.widget.Switch'})
            self.click(coords)
            layout = self.wait_for_text("OK")
            coords = self.get_bounds(layout, "node", {'text': 'OK'})
            self.click(coords)
            time.sleep(3)

    def generate_random_coordinates(self):
        latitude = random.uniform(-90, 90)
        longitude = random.uniform(-180, 180)
        return latitude, longitude

    def start(self):
        mail = self.email_server

        self.wait_for_text("Messenger")
        for emu_name in self.emu_names:
            geo = self.generate_random_coordinates()
            subprocess.run([self.dnconsole, "locate", "--name", emu_name, "--LLI", f"{geo[0]},{geo[1]}"], capture_output=True, text=True)
        time.sleep(1)
        if self.proxy is not None:
            self.set_proxy(self.proxy)

        if self.change_ad_id == "yes":
            subprocess.run([self.adb, "-s", self.adb_id, "shell", "am", "start", "-n", "com.google.android.gms/com.google.android.gms.ads.settings.AdsSettingsActivity"], capture_output=True, text=True)
            layout = self.wait_for_text("Reset advertising ID")
            coords = self.get_bounds(layout, "node", {'text': 'Reset advertising ID'})
            self.click(coords)
            layout = self.wait_for_text("This will replace your advertising ID")
            coords = self.get_bounds(layout, "node", {'text': 'OK'})
            self.click(coords)
            time.sleep(1)
            subprocess.run([self.adb, "-s", self.adb_id, "shell", "am", "force-stop", "com.google.android.gms"], capture_output=True, text=True)
            time.sleep(1)

        for _ in range(self.account_count):
            log.info("Downloading profile picture...")
            profile_jpg = f"profile{slugify(self.adb_id)}.jpg"
            if os.path.exists(profile_jpg):
                os.remove(profile_jpg)
            r = requests.get("https://thispersondoesnotexist.com/")
            with open(profile_jpg, "wb") as f:
                f.write(r.content)

            subprocess.run([self.adb, "-s", self.adb_id, "shell", "pm", "clear", "com.instagram.android"], capture_output=True, text=True)
            subprocess.run([self.adb, "-s", self.adb_id, "shell", "monkey", "-p", "com.instagram.android", "-c", "android.intent.category.LAUNCHER", "1"], capture_output=True, text=True)
            
            layout = self.wait_for_text("Log in")
            coords = self.get_bounds(layout, "node", {'text': 'Create new account'})
            self.click(coords)

            layout = self.wait_for_text("Sign up with email")
            coords = self.get_bounds(layout, "node", {'text': 'Sign up with email'})
            self.click(coords)

            layout = self.wait_for_text("your email")
            coords = self.get_bounds(layout, "node", {'text': 'Email'})
            self.click(coords)

            email, name, domain = mail.generate_email()
            self.type_text(email)
            coords = self.get_bounds(layout, "node", {'text': 'Next'})
            self.click(coords)

            if self.wait_for_text("I didn’t get the code", timeout=self.wait_time):
                layout = self.get_layout()
                coords = self.get_bounds(layout, "node", {"text": "I didn’t get the code"})
                self.click(coords)
            else:
                continue

            layout = self.wait_for_text("Resend confirmation code")
            coords = self.get_bounds(layout, "node", {"text": "Resend confirmation code"})
            self.click(coords)

            code = None
            wait_time = 0
            while not self.stop_event.is_set():
                if wait_time > self.wait_time:
                    break
                is_found = False
                if mail.name == "outlook":
                    mails = mail.check_inbox(email)
                else:
                    mails = mail.check_inbox(name, domain)
                for m in mails:
                    if "Instagram code" in m["subject"]:
                        code = m["subject"].split(" ")[0]
                        log.info(f"Mail OTP: {code}")
                        is_found = True
                        break
                if is_found:
                    break
                time.sleep(1)
                wait_time += 1

            if code is None:
                continue

            layout = self.wait_for_text("Confirmation code")
            coords = self.get_bounds(layout, "node", {"text": "Confirmation code"})
            self.click(coords)
            self.type_text(code)
            layout = self.wait_for_text("Next")
            coords = self.get_bounds(layout, "node", {"text": "Next"})
            self.click(coords)

            layout = self.wait_for_text("Password")
            coords = self.get_bounds(layout, "node", {"text": "Password"})
            self.click(coords)
            self.type_text(self.password)
            coords = self.get_bounds(layout, "node", {"text": "Next"})
            self.click(coords)
            
            layout = self.wait_for_text("Not now")
            coords = self.get_bounds(layout, "node", {"text": "Not now"})
            self.click(coords)

            layout = self.wait_for_text("Set date")
            picker = self.find_element("node", {"class": "android.widget.NumberPicker", "index": "0"}, layout=layout)
            element = self.find_element("node", {"class": "android.widget.Button", "index": "0"}, parent=picker)
            coords = self.get_coords_from_element(element)

            for _ in range(random.randint(1, 10)):
                self.click(coords)
                time.sleep(0.1)

            picker = self.find_element("node", {"class": "android.widget.NumberPicker", "index": "1"}, layout=layout)
            element = self.find_element("node", {"class": "android.widget.Button", "index": "0"}, parent=picker)
            coords = self.get_coords_from_element(element)

            for _ in range(random.randint(1, 10)):
                self.click(coords)
                time.sleep(0.1)

            picker = self.find_element("node", {"class": "android.widget.NumberPicker", "index": "2"}, layout=layout)
            element = self.find_element("node", {"class": "android.widget.Button", "index": "0"}, parent=picker)
            coords = self.get_coords_from_element(element)

            for _ in range(random.randint(19, 39)):
                self.click(coords)
                time.sleep(0.1)

            coords = self.get_bounds(layout, "node", {"text": "SET"})
            self.click(coords)
            time.sleep(1)

            layout = self.wait_for_text("Next")
            coords = self.get_bounds(layout, "node", {"text": "Next"})
            self.click(coords)

            layout = self.wait_for_text("Full name")
            coords = self.get_bounds(layout, "node", {"text": "Full name"})
            self.click(coords)
            first_name, last_name = random_name(self.country)
            self.type_text(f"{first_name} {last_name}")
            coords = self.get_bounds(layout, "node", {"text": "Next"})
            self.click(coords)
            
            layout = self.wait_for_text("username")
            instagram_username = self.find_element("node", {"class": "android.widget.EditText"}, layout=layout)["text"]
            coords = self.get_bounds(layout, "node", {"text": "Next"})
            self.click(coords)

            layout = self.wait_for_multi_text(["I agree", "suspend"])
            if "suspend" in layout:
                log.info(f"Account suspended")
                log.warn(f"!!!SYSTEM DETECTED!!!")
                break
            coords = self.get_bounds(layout, "node", {"text": "I agree"})
            self.click(coords)

            layout = self.wait_for_multi_text(["Add picture", "suspend"])
            if "suspend" in layout:
                log.info(f"Account suspended")
                log.warn(f"!!!SYSTEM DETECTED!!!")
                break
            coords = self.get_bounds(layout, "node", {"text": "Add picture"})
            self.click(coords)

            log.info(f"Pushing profile picture to {self.adb_id}: {profile_jpg}")
            subprocess.run([self.adb, "-s", self.adb_id, "push", f"./{profile_jpg}", "/sdcard/Pictures/profile.jpg"], capture_output=True, text=True)

            layout = self.wait_for_text("Choose from Gallery")
            coords = self.get_bounds(layout, "node", {"text": "Choose from Gallery"})
            self.click(coords)

            if os.path.exists(profile_jpg):
                os.remove(profile_jpg)

            layout = self.wait_for_multi_text(["ALLOW", "profile.jpg"], timeout=5)
            if layout is not None and "ALLOW" in layout:
                coords = self.get_bounds(layout, "node", {"text": "ALLOW"})
                self.click(coords)

            layout = self.wait_for_multi_text(["profile.jpg", "suspended"])
            if "profile.jpg" in layout:
                coords = self.get_bounds(layout, "node", {"text": "profile.jpg"})
                self.click(coords)

            layout = self.wait_for_multi_text(["Done", "suspended"])
            if "Done" in layout:
                coords = self.get_bounds(layout, "node", {"text": "Done"})
                self.click(coords)

            layout = self.wait_for_multi_text(["suspended", "Done", "find your friends", "Welcome"])
            if layout is None or "suspended" in layout:
                log.info(f"Account suspended")
                log.warn(f"!!!SYSTEM DETECTED!!!")
                break
            elif "Done" in layout:
                coords = self.get_bounds(layout, "node", {"text": "Done"})
                self.click(coords)
                layout = self.wait_for_multi_text(["suspended", "Done", "find your friends", "Welcome"], timeout=10)

            if "Done" in layout or "suspended" in layout:
                log.warn(f"!!!SYSTEM DETECTED!!!")
                # log.info(f"Going to wait 1min before creating a new account...")
                # self.countdown(60)
                break

            if self.is_twofa:
                self.enable_2fa(email, self.password)
            else:
                twofa = None

            if twofa == "SUSPENDED":
                log.warn(f"!!!SYSTEM DETECTED!!!")
                break

            # email = "80si7r9soa8@knmcadibav.com"
            # instagram_username = "hasiberisha"
            # self.get_cookies_browser(email, "rockjeev")
            
            log.info("Collecting account data...")
            # cookies = self.get_cookies_http(email, self.password)
            print("-" * terminal_width())
            log.success(f"e-Mail: {email}")
            log.success(f"Password: {self.password}")
            # log.success(f"Cookies: {cookies}")
            log.success(f"Username: {instagram_username}")
            print("-" * terminal_width())
            final_data = f"{email}|{self.password}|{instagram_username}"
            with open(f"instagram_accounts.txt", "a") as f:
                f.write(f"{final_data}\n")
            # input("> ")


    def enable_2fa(self, email, password):
        input("> ")


    def get_cookies_browser(self, email, password):
        subprocess.run([self.adb, "-s", self.adb_id, "shell", "pm", "clear", "com.automator.browser"], capture_output=True, text=True)
        subprocess.run([self.adb, "-s", self.adb_id, "shell", "monkey", "-p", "com.automator.browser", "-c", "android.intent.category.LAUNCHER", "1"], capture_output=True, text=True)
        self.wait_for_text("Google")
        time.sleep(5)

        # adb shell "curl -X POST -d 'url=aHR0cHM6Ly93d3cuZmFjZWJvb2suY29t' 'http://localhost:3001/get-cookie' 2>/dev/null"
        self.open_browser_url("https://www.instagram.com/accounts/login/?next=%2F&source=mobile_nav")
        self.wait_for_text("Instagram")
        self.wait_for_browser_loading()

        self.wait_for_browser_elements(["input[aria-label^='Username']", "input[aria-label^='Phone number']"])
        time.sleep(1)
        html = self.execute_js("return document.body.innerHTML;").lower()
        if "log in with facebook" in html or "continue with facebook" in html:
            # old ui
            self.execute_js("""document.querySelector("input[aria-label^='Phone number']").focus();""")
        else:
            self.execute_js("""document.querySelector("input[aria-label^='Username']").focus();""")
        
        self.type_text(email)
        self.execute_js("""document.querySelector("input[aria-label='Password']").focus();""")
        self.type_text(password)
        self.execute_js("""Array.from(document.querySelectorAll("button")).find(el => el.textContent.trim() == "Log in").click();""")
        html = self.wait_for_browser_texts(["unusual login attempt"])

        if "unusual login attempt" in html:
            mail = self.email_server
            self.execute_js("""Array.from(document.querySelectorAll("div[role='button']")).find(el => el.textContent.trim() == "Continue").click();""")
            self.wait_for_browser_texts(["Enter Your Security Code"])

            code = None
            wait_time = 0
            nodes = email.split("@")
            name = nodes[0]
            domain = nodes[1]
            while not self.stop_event.is_set():
                if wait_time > self.wait_time:
                    break
                is_found = False
                if mail.name == "outlook":
                    mails = mail.check_inbox(email)
                else:
                    mails = mail.check_inbox(name, domain)
                for m in mails:
                    if "Verify your account" == m["subject"]:
                        body = mail.read_email(m["id"], name, domain)["body"]
                        code = self.extract_verification_otp_from_mail_text(body)
                        log.info(f"Mail OTP: {code}")
                        is_found = True
                        break
                if is_found:
                    break
                time.sleep(1)
                wait_time += 1

            if code is None:
                log.warn("OTP didn't receive")
                return
            self.execute_js("""document.querySelector("input[aria-label='Security code']").focus();""")
            self.type_text(code)
            self.execute_js("""Array.from(document.querySelectorAll("div[role='button']")).find(el => el.textContent.trim() == "Submit").click();""")

    def extract_verification_otp_from_mail_text(self, text):
        if self.stop_event.is_set():
            raise Exception("KeyboardInterrupt!")
        pattern = r'\>([0-9]){6}\<'
        match = re.search(pattern, text)

        if match:
            return match.group()
        else:
            return None

    def wait_for_browser_texts(self, texts):
        count = 0
        while True:
            if count > self.wait_time:
                break
            is_found = False
            html = self.execute_js("return document.body.innerHTML;").lower()
            for text in texts:
                if text.lower() in html:
                    is_found = True
                    break
            if is_found:
                break
            count += 1
        return self.execute_js("return document.body.innerHTML;").lower()

    def wait_for_browser_elements(self, selectors):
        count = 0
        while True:
            if count > self.wait_time:
                break
            is_found = False
            for selector in selectors:
                code = f"""return document.querySelectorAll("{selector}").length;"""
                element_count = self.execute_js(code)
                if int(element_count) > 0:
                    is_found = True
                    break
            if is_found:
                break
            count += 1
    
    def execute_js(self, code):
        encoded_code = base64.b64encode(code.encode()).decode()
        proc = subprocess.run(
            [
                self.adb, 
                "-s", 
                self.adb_id, 
                "shell", 
                "curl", 
                "-X", 
                "POST", 
                "-d", f"code={encoded_code}", 
                "http://localhost:3001/execute-js"
            ], 
            capture_output=True, 
            text=True,
            encoding="utf-8"
        )
        return proc.stdout

    def open_browser_url(self, url):
        encoded_url = base64.b64encode(url.encode()).decode()
        subprocess.run(
            [
                self.adb, 
                "-s", 
                self.adb_id, 
                "shell", 
                "curl", 
                "-X", 
                "POST", 
                "-d", f"url={encoded_url}", 
                "http://localhost:3001/open-url"
            ], 
            capture_output=True, 
            text=True,
            encoding="utf-8"
        )
        time.sleep(2)
        self.wait_for_browser_loading()
    
    def wait_for_browser_loading(self):
        count = 0
        while True:
            if count > self.wait_time:
                break
            proc = subprocess.run(
                [
                    self.adb, 
                    "-s", 
                    self.adb_id, 
                    "shell", 
                    "curl", 
                    "-X", 
                    "GET", 
                    "http://localhost:3001/is-loading"
                ], 
                capture_output=True, 
                text=True,
                encoding="utf-8"
            )
            if proc.stdout.strip() == "false":
                break
            count += 1

    def get_cookies_http(self, email, password):
        try:
            IG_SIG_KEY = "109513c04303341a7daf27bb41b268e633b30dcc65a3fe14503f743176113869"
            USER_AGENT = "Instagram 27.0.0.7.97 Android (18/4.3; 320dpi; 720x1280; Xiaomi; HM 1SW; armani; qcom; en_US)"

            device_id = f"android-{hashlib.md5(str(random.randint(0, 9999)).encode()).hexdigest()}{random.randint(0, 9)}"
            data = {
                "username": email,
                "password": password,
                "_csrftoken": "missing",
                "_uuid": str(uuid.uuid4()),
                "device_id": device_id,
                "login_attempt_count": 0
            }
            body = json.dumps(data)
            hash = hmac.new(IG_SIG_KEY.encode(), body.encode(), hashlib.sha256).hexdigest()
            signed_body = f"{hash}.{body}"
            url = "https://i.instagram.com/api/v1/accounts/login/"
            headers = {
                "User-Agent": USER_AGENT
            }
            payload = {
                "ig_sig_key_version": "4",
                "signed_body": signed_body
            }
            response = requests.post(url, headers=headers, data=payload)
            cookie_str = ""
            log.info(f"Status Code: {response.status_code}")
            log.info(f"Status: {response.json().get("status")}")
            log.info(response.json())
            if response.status_code == 200 and response.json().get("status") == "ok":
                cookies = response.cookies.get_dict()
                for k, v in cookies.items():
                    cookie_str += f"{k}={v};"
                cookie_str = cookie_str[:-1]
                return cookie_str
        except Exception as e:
            log.error(e)
        return None

    

    def parse_cookies(self, json_cookies):
        if self.stop_event.is_set():
            raise Exception("KeyboardInterrupt!")
        s = ""
        for c in json_cookies:
            s += f"{c['name']}={c['value']};"

        return s[:-1]

    def wait_for_text(self, text, timeout=-1):
        if timeout == -1:
            timeout = self.wait_time
        log.info(f"Waiting for text: {text}")
        count = 0
        while not self.stop_event.is_set():
            layout = self.get_layout()
            if text in layout:
                return layout

            if count >= timeout:
                return None
            time.sleep(1)
            count += 1
        if self.stop_event.is_set():
            raise Exception("KeyboardInterrupt!")

    def wait_for_multi_text(self, texts, timeout=-1):
        if timeout == -1:
            timeout = self.wait_time
        log.info(f"Waiting for multi text: {texts}")
        count = 0
        while not self.stop_event.is_set():
            layout = self.get_layout()
            for text in texts:
                if text in layout:
                    return layout

            if count >= timeout:
                return None
            time.sleep(1)
            count += 1
        if self.stop_event.is_set():
            raise Exception("KeyboardInterrupt!")

    def get_layout(self):
        if self.stop_event.is_set():
            raise Exception("KeyboardInterrupt!")
        tmp_folder = tempfile.gettempdir()
        view_xml = os.path.join(tmp_folder, f"view{slugify(self.adb_id)}.xml")
        if os.path.exists(view_xml):
            os.remove(view_xml)
        subprocess.run([self.adb, "-s", self.adb_id, "shell", "uiautomator", "dump", "/sdcard/view.xml"], capture_output=True, text=True)
        subprocess.run([self.adb, "-s", self.adb_id, "pull", "/sdcard/view.xml", view_xml], capture_output=True, text=True)

        if not os.path.exists(view_xml):
            return ""

        with open(view_xml, "rb") as f:
            content = f.read()

        return content.decode("utf-8")

    def get_bounds(self, layout, tag, props, index=0, retry=0):
        if self.stop_event.is_set():
            raise Exception("KeyboardInterrupt!")
        if layout is None:
            return None, None
        soup = BeautifulSoup(layout, 'lxml-xml')
        elements = soup.find_all(tag, props)
        if len(elements) == 0 and retry == 0:
            time.sleep(1)
            return self.get_bounds(self.get_layout(), tag, props, index, retry=1)

        element = elements[index]
        bounds = element.get('bounds')
        match = re.search(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
        if match:
            left, top, right, bottom = map(int, match.groups())
            center_x = (left + right) // 2
            center_y = (top + bottom) // 2
            return center_x, center_y
        return None, None

    def click(self, coords):
        if self.stop_event.is_set():
            raise Exception("KeyboardInterrupt!")
        subprocess.run([self.adb, "-s", self.adb_id, "shell", "input", "tap", f"{coords[0]}", f"{coords[1]}"], capture_output=True, text=True)

    def type_text(self, text):
        if self.stop_event.is_set():
            raise Exception("KeyboardInterrupt!")
        # Escape spaces because adb expects '%s' instead of spaces
        escaped_text = text.replace(' ', '%s')
        subprocess.run([self.adb, "-s", self.adb_id, "shell", "input", "text", escaped_text], capture_output=True, text=True)

    def find_element(self, tag, props, layout=None, parent=None):
        if self.stop_event.is_set():
            raise Exception("KeyboardInterrupt!")
        if layout is not None:
            soup = BeautifulSoup(layout, 'lxml-xml')
        elif parent is not None:
            soup = parent
        else:
            raise Exception("Layout or parent is required")
        element = soup.find(tag, props)
        return element

    def get_coords_from_element(self, element):
        if self.stop_event.is_set():
            raise Exception("KeyboardInterrupt!")
        match = re.search(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", element.get('bounds'))
        if match:
            left, top, right, bottom = map(int, match.groups())
            center_x = (left + right) // 2
            center_y = (top + bottom) // 2
            return center_x, center_y
        return None, None

    def countdown(self, seconds):
        if self.stop_event.is_set():
            raise Exception("KeyboardInterrupt!")
        while seconds > 0:
            if self.stop_event.is_set():
                raise Exception("KeyboardInterrupt!")
            # Calculate minutes and seconds
            mins, secs = divmod(seconds, 60)
            # Format the time as MM:SS
            time_format = f'[ Timer: {mins:02d}:{secs:02d} ]'
            # Print the time and overwrite the line
            sys.stdout.write(f'\r{yellow(time_format)}')  # \r moves cursor to the start of the line
            sys.stdout.flush()
            time.sleep(1)  # Wait for 1 second
            seconds -= 1

        log.info("\n* Time's up!")  # Print message when countdown ends

    def handle_dialog_prompt(self, layout):
        if self.stop_event.is_set():
            raise Exception("KeyboardInterrupt!")
        coords = self.get_bounds(layout, "node", {"content-desc": "No thanks"})
        if coords[0] == None:
            subprocess.run([self.adb, "-s", self.adb_id, "shell", "input", "keyevent", "61"], capture_output=True, text=True)
            time.sleep(1)
            subprocess.run([self.adb, "-s", self.adb_id, "shell", "input", "keyevent", "61"], capture_output=True, text=True)
            time.sleep(1)
            subprocess.run([self.adb, "-s", self.adb_id, "shell", "input", "keyevent", "62"], capture_output=True, text=True)
        else:
            self.click(coords)

        self.wait_for_text("Continue using data for Facebook?")
        subprocess.run([self.adb, "-s", self.adb_id, "shell", "input", "keyevent", "61"], capture_output=True, text=True)
        time.sleep(1)
        subprocess.run([self.adb, "-s", self.adb_id, "shell", "input", "keyevent", "62"], capture_output=True, text=True)
        time.sleep(1)

    def get_bounds_by_css_selector(self, layout, selector):
        if self.stop_event.is_set():
            raise Exception("KeyboardInterrupt!")
        if layout is None:
            return None, None
        soup = BeautifulSoup(layout, 'lxml-xml')
        element = soup.select_one(selector)
        bounds = element.get('bounds')
        match = re.search(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
        if match:
            left, top, right, bottom = map(int, match.groups())
            center_x = (left + right) // 2
            center_y = (top + bottom) // 2
            return center_x, center_y
        return None, None

    def get_screen_size(self):
        if self.stop_event.is_set():
            raise Exception("KeyboardInterrupt!")
        size_output = subprocess.run([self.adb, "-s", self.adb_id, "shell", "wm", "size"], capture_output=True, text=True)
        size = size_output.stdout.split(":")[-1].strip()
        width, height = map(int, size.split('x'))
        return width, height

    def extract_otp_from_mail_text(self, text):
        if self.stop_event.is_set():
            raise Exception("KeyboardInterrupt!")
        pattern = r'\>([0-9]){8}\<'
        match = re.search(pattern, text)

        if match:
            return match.group()
        else:
            return None

    def extract_auth_code(self, text):
        if self.stop_event.is_set():
            raise Exception("KeyboardInterrupt!")
        pattern = r'([A-Z0-9]{4} ?)+'
        match = re.search(pattern, text)

        if match:
            return match.group()
        else:
            return None

    def extract_all(self, text, pattern):
        if self.stop_event.is_set():
            raise Exception("KeyboardInterrupt!")
        match = re.search(pattern, text)

        if match:
            return match.groups()
        else:
            return None
