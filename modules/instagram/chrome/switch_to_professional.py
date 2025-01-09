#!/usr/bin/env python3
# coding=utf-8

"""
Copyright (c) 2019 mullaihub developers (https://www.mullaihub.com/accng)
See the file 'LICENSE' for copying permission
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import re
import pyotp
import threading
import signal
import sys

from core.module import Module
from util import log
from util.colorify import bold, red


class AccngModule(Module):
    def __init__(self):
        super().__init__()
        self.name = "Switch to Professional Mode"
        self.description = "Switch all Instagram accounts to professional mode"
        self.author = ["Jeeva"]
        self.options.add("path", "", "Accounts file")
        self.threads = []

    def run(self):
        if not hasattr(self, "email_server"):
            log.error("No mail server is loaded, please load a mail server before running.")
            return

        mail = self.email_server
        path = self.options.get("path")
        if not os.path.exists(path):
            log.error(f"File not found: {path}")
            return

        with open(path, "rt") as f:
            lines = f.read().strip().split("\n")

        # Split lines into three sublists
        sublists = [lines[i::3] for i in range(3)]

        def process_lines(lines):
            for line in lines:
                self.process_account(line, mail)

        # Start threads for each sublist
        for sublist in sublists:
            thread = threading.Thread(target=process_lines, args=(sublist,))
            thread.start()
            self.threads.append(thread)

        # Handle Ctrl+C to exit gracefully
        signal.signal(signal.SIGINT, self.exit_gracefully)

        # Wait for all threads to finish
        for thread in self.threads:
            thread.join()

    def process_account(self, line, mail):
        parts = line.split("|")
        if len(parts) == 3:
            email = parts[0]
            password = parts[1]
            twofa = None
        else:
            email = parts[0]
            password = parts[1]
            twofa = parts[2]

        # Chrome options setup
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_argument("--window-size=600,600")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
                Object.defineProperty(navigator, 'webdriver', {
                  get: () => undefined
                })
                """
            },
        )

        # Your account processing logic here
        try:
            log.info(f"Processing account: {email}")
            driver.get("https://www.instagram.com/")
            username_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username")))
            username_input.send_keys(email)
            password_input = driver.find_element(By.NAME, "password")
            password_input.send_keys(password)
            driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            
            # https://www.instagram.com/accounts/login/?next=https%3A%2F%2Fwww.instagram.com%2Faccounts%2Fconvert_to_professional_account%2F%3F__coig_login%3D1#
            while True:
                url = driver.current_url
                if url.endswith("/"):
                    url = url[:-1]
                if url != "https://www.instagram.com":
                    break
                time.sleep(1)

            content = self.wait_for_texts(driver, ["Check your email", "profile picture", "suspend", "Log in", "6-digit login code generated"])
            if "Log in" in content:
                username_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username")))
                username_input.send_keys(email)
                password_input = driver.find_element(By.NAME, "password")
                password_input.send_keys(password)
                driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
                content = self.wait_for_texts(driver, ["Check your email", "profile picture", "suspend", "Log in", "6-digit login code generated"])
            
            if "6-digit login code generated" in content:
                totp = pyotp.TOTP(twofa.replace(" ", ""))
                current_code = totp.now()
                driver.find_element(By.NAME, "verificationCode").send_keys(f"{current_code}")
                driver.find_element(By.CSS_SELECTOR, "button").click()
                content = self.wait_for_texts(driver, ["Check your email", "profile picture", "suspend"])

            if "Check your email" in content:
                email_parts = email.split("@")
                name = email_parts[0]
                domain = email_parts[1]
                code = None
                wait_time = 0
                time.sleep(5)
                while True:
                    if wait_time > 10:
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
                    log.warn(f"Account '{email}' unable to get OTP")
                    driver.quit()
                    return
                otp_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "email")))
                otp_input.send_keys(code)
                driver.execute_script("""Array.from(document.querySelectorAll("div[role='button']")).find(el => el.textContent.trim() == "Continue").click();""")

            content = self.wait_for_texts(driver, ["suspend", "profile picture"])
            if "suspend" in content:
                log.error(f"Account '{email}' suspended")
                driver.quit()
                return

            driver.get("https://www.instagram.com/accounts/convert_to_professional_account/")
            content = self.wait_for_texts(driver, ["Which Best Describes You", "Edit profile", "Log in"])
            if "Log in" in content:
                log.warn(f"Account '{email}' invalid OTP")
                driver.quit()
                return
            if "Edit profile" in content:
                log.warn(f"Account '{email}' professional mode already enabled")
                driver.quit()
                return
            driver.execute_script("""Array.from(document.querySelectorAll("div[role='button']")).find(el => el.textContent.indexOf("Creator") > -1).click();""")
            time.sleep(1)
            driver.execute_script("""document.querySelector("button[type='button']").click();""")
            self.wait_for_texts(driver, ["Profile Controls"])
            driver.execute_script("""Array.from(document.querySelectorAll("button[type='button']")).find(el => el.textContent.trim() == "Next").click();""")
            self.wait_for_texts(driver, ["Personal blog"])
            driver.execute_script("""Array.from(document.querySelectorAll("div[role='button']")).find(el => el.textContent.indexOf("Personal blog") > -1).click();""")
            time.sleep(1)
            driver.execute_script("""Array.from(document.querySelectorAll("button[type='button']")).find(el => el.textContent.trim() == "Done").click();""")
            self.wait_for_texts(driver, ["Your Instagram creator account is ready"])
            driver.execute_script("""Array.from(document.querySelectorAll("button[type='button']")).find(el => el.textContent.trim() == "Done").click();""")
            self.wait_for_texts(driver, ["Edit profile"])
            log.success(f"Professional mode enabled '{email}'")
        finally:
            driver.quit()

    def exit_gracefully(self, signum, frame):
        log.info("Exiting gracefully...")
        for thread in self.threads:
            if thread.is_alive():
                thread.join()
        sys.exit(0)

    def wait_for_texts(self, driver, texts):
        log.info(f"Wait for texts: {texts}")
        content = ""
        while True:
            content = driver.page_source
            is_found = False
            for text in texts:
                if text in content:
                    is_found = True
                    break
            if is_found:
                break
            time.sleep(1)
        return content
    
    def extract_verification_otp_from_mail_text(self, text):
        pattern = r'\>([0-9]){6}\<'
        match = re.search(pattern, text)

        if match:
            return match.group()[1:][:-1]
        else:
            return None
