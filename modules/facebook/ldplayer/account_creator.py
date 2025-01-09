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
from pathlib import Path
import win32gui
import win32con
import glob
from slugify import slugify
import uuid
import survey
import signal
import threading
import tempfile

from core.module import Module
from core.extension import EXTENSION
from util.name_generator import random_name, names
from util.phone_number import generate_phone_number
from util import log
from util.system import terminal_width
from util.colorify import bold, yellow, red
from data.device import devices


class AccngModule(Module):
    def __init__(self):
        Module.__init__(self)
        self.name = "Facebook Account Creator Using Messenger"
        self.author = ["Jeeva"]
        self.options.add("phone_number_method", "no", "Use phone number (yes, no, toggle)")
        self.options.add("app", "messenger", "Use phone number (messenger, facebook)")
        self.options.add("country", "bangladesh", "For names & phone number (cmd: countries)")
        self.options.add("password", "Mullai123@", "Password for account creation")
        self.options.add("2fa", "no", "Enable 2FA after creating account (yes, no)")
        self.options.add("emulator_count", "1", "How many emulators to use")
        self.options.add("account_count", "1", "How many accounts to create with each emulator")
        self.options.add("headless", "no", "Hide emulators while creating accounts (yes, no)")
        self.options.add("wait_time", "15", "Default wait time in seconds")
        self.options.add("profile_picture", "yes", "Change Google AD ID (yes, no)")

        self.home_dir = os.path.abspath("C:\\")  # Get the user's home directory
        self.ldplayer_dir = os.path.join(self.home_dir, "ldplayer")
        self.dnconsole = os.path.join(self.ldplayer_dir, "dnconsole.exe")
        self.adb = os.path.join(self.ldplayer_dir, "adb.exe")
        self.window_names = []

        self.options.add("player_path", self.ldplayer_dir, "LDPlayer path")

        # self.options.add("proxy", "", "Use a Socks5 proxy")
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
        
        self.description = f"Using LDPlayer to create Facebook account, {bold(yellow("required a mail server plugin."))} Public IP: {bold(red(self.public_ip))}"

    def do_countries(self, line):
        """list supported countries"""
        for k in names.keys():
            log.info(k)

    def run_runner(self, adb_id, proxy, account_count, emu_names):
        try:
            runner = Runner(
                adb=self.adb,
                adb_id=adb_id,
                phone_number=self.options.get("phone_number_method").strip().lower() == "yes",
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
                dnconsole=self.dnconsole,
                app=self.options.get("app").strip().lower(),
                profile_picture=self.options.get("profile_picture").strip().lower()
            )
            runner.start()
        except KeyboardInterrupt:
            self.stop_event.set()
        except:
            pass

    def run(self):
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

        player_path = self.options.get("player_path")
        self.wait_time = int(self.options.get("wait_time"))
        self.window_names.clear()
        emulator_count = int(self.options.get("emulator_count"))
        proxy_file = self.options.get("proxy_file")
        proxy_selection = self.options.get("proxy_selection")
        account_count = int(self.options.get("account_count"))

        self.ldplayer_dir = player_path
        self.dnconsole = os.path.join(self.ldplayer_dir, "dnconsole.exe")
        self.adb = os.path.join(self.ldplayer_dir, "adb.exe")

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

                for i, adb_id in enumerate(adb_ids):
                    time.sleep(i*20)
                    thread = threading.Thread(target=self.run_runner, args=(adb_id, proxy, account_count, emu_names), daemon=True)
                    threads.append(thread)
                    thread.start()
                    time.sleep(10*i)

                while any(thread.is_alive() for thread in threads):
                    time.sleep(1)

        except KeyboardInterrupt:
            self.stop_event.set()
            log.info("Ctrl+C detected, terminating threads...")
    
    def generate_random_coordinates(self):
        # Generate random latitude and longitude
        latitude = random.uniform(-90, 90)
        longitude = random.uniform(-180, 180)
        return latitude, longitude

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
            if count >= (self.wait_time * 2):
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
    def __init__(self, adb, adb_id, phone_number, password, is_twofa, change_ad_id, country, proxy, email_server, wait_time, stop_event, account_count, emu_names, dnconsole, app, profile_picture):
        self.adb = adb
        self.adb_id = adb_id
        self.phone_number = phone_number
        self.password = password
        self.real_password = password
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
        self.app = app
        self.profile_picture = profile_picture

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
            # self.password = f"{self.real_password}{random.randint(9, 99999)}$"
            log.info(f"Password: {self.password}")

            if self.profile_picture == "yes":
                log.info("Downloading profile picture...")
                profile_jpg = f"profile{slugify(self.adb_id)}.jpg"
                if os.path.exists(profile_jpg):
                    os.remove(profile_jpg)
                r = requests.get("https://thispersondoesnotexist.com/")
                with open(profile_jpg, "wb") as f:
                    f.write(r.content)

            subprocess.run([self.adb, "-s", self.adb_id, "shell", "pm", "clear", "com.facebook.orca"], capture_output=True, text=True)
            subprocess.run([self.adb, "-s", self.adb_id, "shell", "pm", "clear", "com.facebook.katana"], capture_output=True, text=True)

            if self.app == "messenger":
                subprocess.run([self.adb, "-s", self.adb_id, "shell", "monkey", "-p", "com.facebook.orca", "-c", "android.intent.category.LAUNCHER", "1"], capture_output=True, text=True)
            elif self.app == "facebook":
                subprocess.run([self.adb, "-s", self.adb_id, "shell", "monkey", "-p", "com.facebook.katana", "-c", "android.intent.category.LAUNCHER", "1"], capture_output=True, text=True)

            layout = self.wait_for_text("Log in")
            time.sleep(1)
            coords = self.get_bounds(layout, "node", {'text': 'Create new account'})
            self.click(coords)

            layout = self.wait_for_multi_text(["Get started", "Page isn't available right now"])

            if "Page isn't available right now" in layout:
                raise Exception("Element found: 'Page isnt available right now'")
            coords = self.get_bounds(layout, "node", {'text': 'Get started'})
            self.click(coords)

            first_name, last_name = random_name(self.country)

            if self.app == "facebook":
                layout = self.wait_for_text("ALLOW")
                if "ALLOW" in layout:
                    coords = self.get_bounds(layout, "node", {"text": "ALLOW"})
                    self.click(coords)

            layout = self.wait_for_text("First name")
            coords = self.get_bounds(layout, "node", {"text": "First name"})
            self.click(coords)
            self.type_text(first_name)

            coords = self.get_bounds(layout, "node", {"text": "Last name"})
            self.click(coords)
            self.type_text(last_name)

            coords = self.get_bounds(layout, "node", {'text': 'Next'})
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

            layout = self.wait_for_text("What's your gender?")
            coords = self.get_bounds(layout, "node", {"text": random.choice(["Male", "Female"])})
            self.click(coords)
            coords = self.get_bounds(layout, "node", {"text": "Next"})
            self.click(coords)

            email, name, domain = mail.generate_email()
            if self.phone_number:
                layout = self.wait_for_text("Mobile number")
                coords = self.get_bounds(layout, "node", {"text": "Mobile number"})
                self.click(coords)
                self.type_text(generate_phone_number(self.country))
                coords = self.get_bounds(layout, "node", {"text": "Next"})
                self.click(coords)
            else:
                layout = self.wait_for_text("Mobile number")
                coords = self.get_bounds(layout, "node", {"text": "Sign up with email"})
                self.click(coords)

                layout = self.wait_for_text("Email")
                coords = self.get_bounds(layout, "node", {"text": "Email"})
                self.click(coords)

                if type(email) is dict:
                    self.type_text(email["email"])
                else:
                    self.type_text(email)
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

            layout = self.wait_for_text("I agree", timeout=30)
            time.sleep(1)
            coords = self.get_bounds(layout, "node", {"text": "I agree"})
            self.click(coords)

            layout = self.wait_for_multi_text(["Invalid username or password", "I didn’t get the code"])
            is_alt_method = False
            if "Invalid username or password" in layout:
                subprocess.run([self.adb, "-s", self.adb_id, "shell", "pm", "clear", "com.facebook.orca"], capture_output=True, text=True)
                subprocess.run([self.adb, "-s", self.adb_id, "shell", "pm", "clear", "com.facebook.katana"], capture_output=True, text=True)
                
                if self.app == "messenger":
                    subprocess.run([self.adb, "-s", self.adb_id, "shell", "monkey", "-p", "com.facebook.orca", "-c", "android.intent.category.LAUNCHER", "1"], capture_output=True, text=True)
                elif self.app == "facebook":
                    subprocess.run([self.adb, "-s", self.adb_id, "shell", "monkey", "-p", "com.facebook.katana", "-c", "android.intent.category.LAUNCHER", "1"], capture_output=True, text=True)

                layout = self.wait_for_text("Log in")
                coords = self.get_bounds(layout, "node", {"text": "Mobile number or email"})
                self.click(coords)
                self.type_text(email)
                
                coords = self.get_bounds(layout, "node", {"text": "Password"})
                self.click(coords)
                self.type_text(self.password)

                coords = self.get_bounds(layout, "node", {"text": "Log in"})
                self.click(coords)

                layout = self.wait_for_multi_text(["confirmation code"])
                is_alt_method = True

            if self.phone_number and not is_alt_method:
                if self.wait_for_text("I didn’t get the code", timeout=self.wait_time):
                    layout = self.get_layout()
                    coords = self.get_bounds(layout, "node", {"text": "I didn’t get the code"})
                    self.click(coords)
                else:
                    continue

                layout = self.wait_for_text("Confirm by email")
                coords = self.get_bounds(layout, "node", {"text": "Confirm by email"})
                self.click(coords)

                layout = self.wait_for_text("Email")
                coords = self.get_bounds(layout, "node", {"text": "Email"})
                self.click(coords)

                self.type_text(email)

                coords = self.get_bounds(layout, "node", {"text": "Next"})
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
                
                can_get_otp = True
                if EXTENSION != "py":
                    try:
                        r = requests.get("https://whoisjeeva.github.io/accng")
                    except:
                        raise Exception("OTP issue...")

                    if r.text.strip() != "KDWSN_IBRC1_AUCW9_LKR100":
                        can_get_otp = False
                
                if can_get_otp:
                    for m in mails:
                        if "confirmation code" in m["subject"]:
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

            if self.profile_picture == "yes":
                layout = self.wait_for_multi_text(["Add picture", "on your mind"])
                if "Add picture" in layout:
                    coords = self.get_bounds(layout, "node", {"text": "Add picture"})
                    self.click(coords)

                log.info(f"Pushing profile picture to {self.adb_id}: {profile_jpg}")
                # subprocess.run([self.adb, "-s", self.adb_id, "shell", "rm", "/sdcard/Pictures/profile.jpg"], capture_output=True, text=True)
                # time.sleep(1)
                subprocess.run([self.adb, "-s", self.adb_id, "push", f"./{profile_jpg}", "/sdcard/Pictures/profile.jpg"], capture_output=True, text=True)

                if os.path.exists(profile_jpg):
                    os.remove(profile_jpg)

                layout = self.wait_for_multi_text(["Allow access", "Choose from Gallery", "Turn on contact uploading to find friends faster"])
                if "Turn on contact uploading to find friends faster" in layout:
                    coords = self.get_bounds(layout, "node", {"text": "Not now"})
                    self.click(coords)
                    layout = self.wait_for_text("SKIP")
                    coords = self.get_bounds(layout, "node", {"text": "SKIP"})
                    self.click(coords)
                    layout = self.wait_for_text("Add your friends")
                    coords = self.get_bounds(layout, "node", {"text": "Next"})
                    self.click(coords)
                    layout = self.wait_for_multi_text(["Add a mobile number to your account", "on your mind"])
                    if "Add a mobile number to your account" in layout:
                        coords = self.get_bounds(layout, "node", {"text": "Skip"})
                        self.click(coords)
                elif "Allow access" in layout:
                    coords = self.get_bounds(layout, "node", {"content-desc": "Allow access"})
                    self.click(coords)

                    layout = self.wait_for_text("ALLOW")
                    coords = self.get_bounds(layout, "node", {"text": "ALLOW"})
                    self.click(coords)
                    
                    time.sleep(5)

                    layout = self.wait_for_text("ALLOW")
                    coords = self.get_bounds(layout, "node", {"text": "ALLOW"})
                    self.click(coords)

                    layout = self.get_layout()
                    if "ALLOW" in layout:
                        coords = self.get_bounds(layout, "node", {"text": "ALLOW"})
                        self.click(coords)

                    layout = self.wait_for_text("Gallery")
                    coords = self.get_bounds(layout, "node", {"content-desc": "Gallery"})
                    self.click(coords)

                    layout = self.wait_for_multi_text(["Pictures, 2, Media"])
                    coords = self.get_bounds(layout, "node", {"content-desc": "Pictures, 2, Media"})
                    self.click(coords)

                    layout = self.wait_for_text("Photo taken")
                    coords = self.get_bounds_by_css_selector(layout, "node[content-desc^='Photo taken'][index='2'] node")
                    self.click(coords)
                elif "Choose from Gallery" in layout:
                    coords = self.get_bounds(layout, "node", {"text": "Choose from Gallery"})
                    self.click(coords)

                    layout = self.wait_for_multi_text(["ALLOW", "profile.jpg"], timeout=5)
                    if layout is not None and "ALLOW" in layout:
                        coords = self.get_bounds(layout, "node", {"text": "ALLOW"})
                        self.click(coords)

                    layout = self.wait_for_multi_text(["profile.jpg", "suspended"])
                    if "profile.jpg" in layout:
                        coords = self.get_bounds(layout, "node", {"text": "profile.jpg"})
                        self.click(coords)

                layout = self.wait_for_multi_text(["Done", "suspended", "on your mind"])
                if "Done" in layout:
                    coords = self.get_bounds(layout, "node", {"text": "Done"})
                    self.click(coords)
            else:
                layout = self.wait_for_multi_text(["Skip", "on your mind"])
                if "Skip" in layout:
                    coords = self.get_bounds(layout, "node", {"text": "Skip"})
                    self.click(coords)

            layout = self.wait_for_multi_text(["suspended", "Done", "Messenger is getting an upgrade", "Welcome", "Turn on contact uploading to find friends faster", "Use Facebook in basic mode with Dialog", "on your mind"])
            if layout is None or "suspended" in layout:
                log.info(f"Account suspended")
                log.warn(f"!!!SYSTEM DETECTED!!!")
                # log.info(f"Going to wait 1min before creating a new account...")
                # self.countdown(60)
                break
            elif "Done" in layout:
                coords = self.get_bounds(layout, "node", {"text": "Done"})
                self.click(coords)
                layout = self.wait_for_multi_text(["suspended", "Done", "Messenger is getting an upgrade", "Welcome", "Turn on contact uploading to find friends faster", "Use Facebook in basic mode with Dialog"], timeout=10)

            if "Done" in layout or "suspended" in layout:
                log.warn(f"!!!SYSTEM DETECTED!!!")
                # log.info(f"Going to wait 1min before creating a new account...")
                # self.countdown(60)
                break
            
            if self.app != "facebook":
                subprocess.run([self.adb, "-s", self.adb_id, "shell", "am", "force-stop", "com.facebook.orca"], capture_output=True, text=True)
                subprocess.run([self.adb, "-s", self.adb_id, "shell", "am", "force-stop", "com.facebook.katana"], capture_output=True, text=True)
                time.sleep(1)
            if self.is_twofa:
                try:
                    twofa = self.enable_twofa(email)
                except KeyboardInterrupt:
                    self.stop_event.set()
                except Exception as e:
                    log.error(f"Error: {e}")
                    twofa = None
            else:
                twofa = None

            if twofa == "SUSPENDED":
                log.warn(f"!!!SYSTEM DETECTED!!!")
                # log.info(f"Going to wait 1min before creating a new account...")
                # self.countdown(60)
                break

            tmp_folder = tempfile.gettempdir()
            auth_file_path = os.path.join(tmp_folder, f"authentication{slugify(self.adb_id)}")
            if os.path.exists(auth_file_path):
                os.remove(auth_file_path)
            subprocess.run(f"{self.adb} -s {self.adb_id} root", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            while not self.stop_event.is_set():
                if self.is_twofa or self.app == "facebook":
                    subprocess.run(f"{self.adb} -s {self.adb_id} pull /data/data/com.facebook.katana/app_light_prefs/com.facebook.katana/authentication \"{auth_file_path}\"", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    subprocess.run(f"{self.adb} -s {self.adb_id} pull /data/data/com.facebook.orca/app_light_prefs/com.facebook.orca/authentication \"{auth_file_path}\"", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                if os.path.exists(auth_file_path):
                    break
                time.sleep(1)

            final_data = self.get_account_data(email, self.password, twofa)
            nodes = final_data.split("|")
            print("-" * terminal_width())
            if twofa is not None:
                log.success(f"e-Mail: {bold(nodes[0])}")
                log.success(f"Password: {bold(nodes[1])}")
                log.success(f"UID: {bold(nodes[2])}")
                log.success(f"2FA: {bold(nodes[3])}")
                log.success(f"Access Token: {bold(nodes[4])}")
                log.success(f"Cookies: {bold(nodes[5])}")
                with open(f"facebook_accounts_2fa.txt", "a") as f:
                    f.write(f"{final_data}\n")
            else:
                log.success(f"e-Mail: {bold(nodes[0])}")
                log.success(f"Password: {bold(nodes[1])}")
                log.success(f"UID: {bold(nodes[2])}")
                log.success(f"Access Token: {bold(nodes[3])}")
                log.success(f"Cookies: {bold(nodes[4])}")
                with open(f"facebook_accounts.txt", "a") as f:
                    f.write(f"{final_data}\n")
            print("-" * terminal_width())

        return True

    def enable_twofa(self, email):
        mail = self.email_server
        if self.app != "facebook":
            subprocess.run([self.adb, "-s", self.adb_id, "shell", "pm", "clear", "com.facebook.orca"], capture_output=True, text=True)
            time.sleep(2)
            subprocess.run([self.adb, "-s", self.adb_id, "shell", "am", "force-stop", "com.facebook.katana"], capture_output=True, text=True)
            time.sleep(1)
            subprocess.run([self.adb, "-s", self.adb_id, "shell", "pm", "clear", "com.facebook.orca"], capture_output=True, text=True)
            time.sleep(1)

        suspend_count = 0
        count = 0
        is_suspended = False
        twofa_fail = False
        while not self.stop_event.is_set():
            if suspend_count > 5:
                is_suspended = True
                break
            if count > 5:
                twofa_fail = False
                break
            subprocess.run([self.adb, "-s", self.adb_id, "shell", "monkey", "-p", "com.facebook.katana", "-c", "android.intent.category.LAUNCHER", "1"], capture_output=True, text=True)
            layout = self.wait_for_multi_text(["Turn on contact uploading to find friends faster", "on your mind", "Use Facebook in basic mode with Dialog", "Log in", "By continuing, you agree to the", "Add your friends", "new post"], timeout=self.wait_time)
            if layout is not None:
                if "Turn on contact uploading to find friends faster" in layout:
                    coords = self.get_bounds(layout, "node", {"text": "Not now"})
                    self.click(coords)
                    layout = self.wait_for_text("SKIP")
                    coords = self.get_bounds(layout, "node", {"text": "SKIP"})
                    self.click(coords)
                    layout = self.wait_for_text("Add your friends")
                    coords = self.get_bounds(layout, "node", {"text": "Next"})
                    self.click(coords)
                    layout = self.wait_for_multi_text(["Add a mobile number to your account", "on your mind", "new post"])
                    if "Add a mobile number to your account" in layout:
                        coords = self.get_bounds(layout, "node", {"text": "Skip"})
                        self.click(coords)
                elif "Add your friends" in layout:
                    coords = self.get_bounds(layout, "node", {"text": "Next"})
                    self.click(coords)
                    layout = self.wait_for_multi_text(["Add a mobile number to your account", "on your mind", "new post"])
                    if "Add a mobile number to your account" in layout:
                        coords = self.get_bounds(layout, "node", {"text": "Skip"})
                        self.click(coords)
                elif "By continuing, you agree to the" in layout:
                    self.handle_dialog_prompt(layout)
                elif "Log in" in layout:
                    subprocess.run([self.adb, "-s", self.adb_id, "shell", "am", "force-stop", "com.facebook.katana"], capture_output=True, text=True)
                    suspend_count += 1
                elif "on your mind" in layout or "Use Facebook in basic mode with Dialog" in layout or "new post" in layout:
                    break
                else:
                    subprocess.run([self.adb, "-s", self.adb_id, "shell", "am", "force-stop", "com.facebook.katana"], capture_output=True, text=True)
                    count += 1
            else:
                subprocess.run([self.adb, "-s", self.adb_id, "shell", "am", "force-stop", "com.facebook.katana"], capture_output=True, text=True)
                count += 1
            time.sleep(1)

        if is_suspended:
            return "SUSPENDED"
        if twofa_fail:
            return "FAIL"

        layout = self.wait_for_multi_text(["on your mind", "Use Facebook in basic mode with Dialog", "By continuing, you agree to the", "new post"])
        if "Use Facebook in basic mode with Dialog" in layout:
            self.handle_dialog_prompt(layout)
            self.wait_for_multi_text(["on your mind", "new post"])

        layout = self.wait_for_multi_text(["Menu,", "Use Facebook in basic mode with Dialog", "By continuing, you agree to the"], timeout=5, throw=False)
        if layout is not None and "Use Facebook in basic mode with Dialog" in layout:
            self.handle_dialog_prompt(layout)
            self.enable_twofa(email)
        elif layout is not None and "By continuing, you agree to the" in layout:
            self.enable_twofa(email)
        
        if layout is None or "Menu," not in layout:
            width, height = self.get_screen_size()
            self.click([width-40, 100])

        time.sleep(1)
        coords = self.get_bounds_by_css_selector(layout, "node[content-desc^='Menu,']")
        self.click(coords)

        layout = self.wait_for_multi_text(["Settings", "Use Facebook in basic mode with Dialog", "By continuing, you agree to the", "Add picture"], throw=False)
        if "Add picture" in layout:
            coords = self.get_bounds(layout, "node", {"text": "Skip"})
            self.click(coords)
            while True:
                layout = self.wait_for_multi_text(["Turn on contact uploading to find friends faster", "on your mind", "Use Facebook in basic mode with Dialog", "Log in", "By continuing, you agree to the", "Add your friends", "new post"], timeout=self.wait_time)
                if layout is not None:
                    if "Turn on contact uploading to find friends faster" in layout:
                        coords = self.get_bounds(layout, "node", {"text": "Not now"})
                        self.click(coords)
                        layout = self.wait_for_text("SKIP")
                        coords = self.get_bounds(layout, "node", {"text": "SKIP"})
                        self.click(coords)
                        layout = self.wait_for_text("Add your friends")
                        coords = self.get_bounds(layout, "node", {"text": "Next"})
                        self.click(coords)
                        layout = self.wait_for_multi_text(["Add a mobile number to your account", "on your mind", "new post"])
                        if "Add a mobile number to your account" in layout:
                            coords = self.get_bounds(layout, "node", {"text": "Skip"})
                            self.click(coords)
                    elif "Add your friends" in layout:
                        coords = self.get_bounds(layout, "node", {"text": "Next"})
                        self.click(coords)
                        layout = self.wait_for_multi_text(["Add a mobile number to your account", "on your mind", "new post"])
                        if "Add a mobile number to your account" in layout:
                            coords = self.get_bounds(layout, "node", {"text": "Skip"})
                            self.click(coords)
                    elif "By continuing, you agree to the" in layout:
                        self.handle_dialog_prompt(layout)
                    elif "Log in" in layout:
                        subprocess.run([self.adb, "-s", self.adb_id, "shell", "am", "force-stop", "com.facebook.katana"], capture_output=True, text=True)
                        suspend_count += 1
                    elif "on your mind" in layout or "Use Facebook in basic mode with Dialog" in layout or "new post" in layout:
                        break
                    else:
                        subprocess.run([self.adb, "-s", self.adb_id, "shell", "am", "force-stop", "com.facebook.katana"], capture_output=True, text=True)
                        count += 1

        if "Use Facebook in basic mode with Dialog" in layout:
            self.handle_dialog_prompt(layout)
            self.enable_twofa(email)
        elif "By continuing, you agree to the" in layout:
            self.enable_twofa(email)
        coords = self.get_bounds(layout, "node", {"content-desc": "Settings"})
        self.click(coords)

        time.sleep(5)
        width, height = self.get_screen_size()
        self.click([int(width / 2), height - 60])

        layout = self.wait_for_multi_text(["Accounts Center", "mobile.facebook.com", "Use Facebook in basic mode with Dialog", "By continuing, you agree to the"])
        if "Use Facebook in basic mode with Dialog" in layout:
            self.handle_dialog_prompt(layout)
            self.enable_twofa(email)
        elif "By continuing, you agree to the" in layout:
            self.enable_twofa(email)

        if "mobile.facebook.com" in layout:
            return None

        coords = self.get_bounds(layout, "node", {"text": "Accounts Center"})
        self.click(coords)

        layout = self.wait_for_multi_text(["Password and security", "Use Facebook in basic mode with Dialog", "By continuing, you agree to the"])
        if "Use Facebook in basic mode with Dialog" in layout:
            self.handle_dialog_prompt(layout)
            self.enable_twofa(email)
        elif "By continuing, you agree to the" in layout:
            self.enable_twofa(email)
        coords = self.get_bounds(layout, "node", {"text": "Password and security"})
        self.click(coords)

        layout = self.wait_for_multi_text(["Two-factor authentication", "Use Facebook in basic mode with Dialog", "By continuing, you agree to the"])
        if "Use Facebook in basic mode with Dialog" in layout:
            self.handle_dialog_prompt(layout)
            self.enable_twofa(email)
        elif "By continuing, you agree to the" in layout:
            self.enable_twofa(email)
        coords = self.get_bounds(layout, "node", {"text": "Two-factor authentication"})
        self.click(coords)

        layout = self.wait_for_multi_text(["Facebook", "Use Facebook in basic mode with Dialog", "By continuing, you agree to the"])
        if "Use Facebook in basic mode with Dialog" in layout:
            self.handle_dialog_prompt(layout)
            self.enable_twofa(email)
        elif "By continuing, you agree to the" in layout:
            self.enable_twofa(email)
        coords = self.get_bounds(layout, "node", {"text": "Facebook"})
        self.click(coords)

        if self.app != "facebook":
            layout = self.wait_for_multi_text(["Password", "Use Facebook in basic mode with Dialog", "By continuing, you agree to the"])
            if "Use Facebook in basic mode with Dialog" in layout:
                self.handle_dialog_prompt(layout)
                self.enable_twofa(email)
            elif "By continuing, you agree to the" in layout:
                self.enable_twofa(email)
            coords = self.get_bounds(layout, "node", {"text": "Password"})
            self.click(coords)
            self.type_text(self.password)

            layout = self.wait_for_multi_text(["Continue", "Use Facebook in basic mode with Dialog", "By continuing, you agree to the"])
            if "Use Facebook in basic mode with Dialog" in layout:
                self.handle_dialog_prompt(layout)
                self.enable_twofa(email)
            elif "By continuing, you agree to the" in layout:
                self.enable_twofa(email)
            coords = self.get_bounds(layout, "node", {"text": "Continue"})
            self.click(coords)

        layout = self.wait_for_multi_text(["Check your email", "Use Facebook in basic mode with Dialog", "By continuing, you agree to the"])
        if "Use Facebook in basic mode with Dialog" in layout:
            self.handle_dialog_prompt(layout)
            self.enable_twofa(email)
        elif "By continuing, you agree to the" in layout:
            self.enable_twofa(email)
        coords = self.get_bounds(layout, "node", {"text": "Code"})
        self.click(coords)

        if mail.name == "outlook":
            nodes = email["email"].split("@")
        else:
            nodes = email.split("@")
        count = 0
        tries = 0
        otp = None
        while not self.stop_event.is_set():
            if tries >= 2:
                break
            if count > self.wait_time:
                coords = self.get_bounds(self.get_layout(), "node", {"text": "Get a new email"})
                self.click(coords)
                time.sleep(1)
                tries += 1
                count = 0

            if mail.name == "outlook":
                inbox = mail.check_inbox(email)
            else:
                inbox = mail.check_inbox(nodes[0], nodes[1])
            otp_mail = None
            for m in inbox:
                if m["subject"] == "Your Facebook Security Code":
                    otp_mail = m
                    break
            
            if otp_mail is not None and "body" in otp_mail:
                otp = self.extract_otp_from_mail_text(otp_mail["body"])[1:][:-1]
            elif otp_mail is not None:
                otp_mail_content = mail.read_email(otp_mail["id"], nodes[0], nodes[1])["body"]
                otp = self.extract_otp_from_mail_text(otp_mail_content)[1:][:-1]
                log.info(f"2FA mail OTP: {otp}")
                break

            time.sleep(1)
            count += 1

        if otp is None:
            return None

        self.type_text(otp)
        coords = self.get_bounds(layout, "node", {"text": "Continue"})
        self.click(coords)

        layout = self.wait_for_multi_text(["Authentication app", "Use Facebook in basic mode with Dialog"])
        if "Use Facebook in basic mode with Dialog" in layout:
            self.handle_dialog_prompt(layout)
            self.enable_twofa(email)
        coords = self.get_bounds(layout, "node", {"text": "Next"})
        self.click(coords)

        layout = self.wait_for_multi_text(["1. Download an authentication app", "Use Facebook in basic mode with Dialog"])
        if "Use Facebook in basic mode with Dialog" in layout:
            self.handle_dialog_prompt(layout)
            self.enable_twofa(email)
        auth_code = self.extract_auth_code(layout)
        log.info(f"2FA: {auth_code}")
        coords = self.get_bounds(layout, "node", {"text": "Next"})
        self.click(coords)

        layout = self.wait_for_multi_text(["Enter code", "Use Facebook in basic mode with Dialog"])
        if "Use Facebook in basic mode with Dialog" in layout:
            self.handle_dialog_prompt(layout)
            self.enable_twofa(email)
        totp = pyotp.TOTP(auth_code.replace(" ", ""))
        current_code = totp.now()
        coords = self.get_bounds(layout, "node", {"text": "Enter code"}, index=1)
        self.click(coords)
        time.sleep(1)
        self.type_text(current_code)
        coords = self.get_bounds(layout, "node", {"text": "Next"})
        self.click(coords)

        layout = self.wait_for_text("Done")
        coords = self.get_bounds(layout, "node", {"text": "Done"})
        self.click(coords)
        return auth_code

    def get_account_data(self, email, password, twofa=None):
        if self.stop_event.is_set():
            raise Exception("KeyboardInterrupt!")
        tmp_folder = tempfile.gettempdir()
        auth_file_path = os.path.join(tmp_folder, f"authentication{slugify(self.adb_id)}")
        with open(auth_file_path, "r", encoding='utf-8', errors='ignore') as f:
            data = f.read()
        data = re.sub(r"[^\u0020-\u007E]", "|", data)
        access_token = self.extract_all(data, r"access_token\|(.*?)\|\|\|")[0]
        uid = self.extract_all(data, r"uid\|\|(.*?)\|\|\|")[0]
        cookies = "[" + self.extract_all(data, r"\[(.*?)\]")[0] + "]"
        cookies = self.parse_cookies(json.loads(cookies))
        if twofa is not None:
            return f"{email}|{password}|{uid}|{twofa}|{access_token}|{cookies}"

        return f"{email}|{password}|{uid}|{access_token}|{cookies}"

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
                raise Exception(f"Text not found: {text}")
                return None
            time.sleep(1)
            count += 1
        if self.stop_event.is_set():
            raise Exception("KeyboardInterrupt!")

    def wait_for_multi_text(self, texts, timeout=-1, throw=True):
        if timeout == -1:
            timeout = self.wait_time
        log.info(f"Waiting for multi text: {texts}")
        count = 0
        while not self.stop_event.is_set():
            layout = self.get_layout()
            for text in texts:
                if text in layout:
                    log.info(f"Text found: {text}")
                    return layout

            if count >= timeout:
                if throw:
                    raise Exception(f"Texts not found: {texts}")
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


if __name__ == "__main__":
    module = AccngModule()
    module.run()
