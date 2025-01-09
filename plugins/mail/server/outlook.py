#!/usr/bin/env python3
# coding=utf-8

"""
Copyright (c) 2019 mullaihub developers (https://www.mullaihub.com/accng)
See the file 'LICENSE' for copying permission
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import pyotp
import os

from core.module import Plugin
from util import log


class AccngPlugin(Plugin):
    def __init__(self, module):
        Plugin.__init__(self, module)
        self.name = "Outlook Mail Provider Plugin"
        self.description = "You can read and generate (from a file) emails from outlook.com and the email format should be e-Mail|Password|2FA"
        self.author = ["Jeeva"]
        self.options.add("path", "", "Outlook e-Mail list file")

    def run(self):
        path = self.options.get("path").strip()
        if not os.path.exists(path):
            raise Exception("e-Mail list file not found")
        self.module.email_server = OutlookMail(path)
        log.info("Outlook API loaded")


class OutlookMail:
    def __init__(self, path):
        self.name = "outlook"
        with open(path, "r") as f:
            lines = f.read().strip().split("\n")
        self.emails = []
        for line in lines:
            nodes = line.split("|")
            if len(nodes) >= 3:
                self.emails.append({ "email": nodes[0], "password": nodes[1], "2fa": nodes[2] })
            else:
                self.emails.append({ "email": nodes[0], "password": nodes[1], "2fa": "" })
        self.index = 0


    def generate_email(self):
        email = self.emails[self.index]
        self.index += 1
        return email, None, None

    def check_inbox(self, email):
        chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument('--disable-logging')  # Disable logging option
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        driver.get('https://login.live.com/login.srf')

        log.info("Initializing Outlook mail server...")
        # Wait for email input, enter the email, and proceed
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "loginfmt"))
        )
        email_input.send_keys(email["email"])
        email_input.send_keys(Keys.RETURN)

        # Wait for password input, enter the password, and proceed
        password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "passwd"))
        )
        password_input.send_keys(email["password"])
        password_input.send_keys(Keys.RETURN)

        log.info("Handling Outlook authentication...")
        otp_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "otc"))
        )

        totp = pyotp.TOTP(email["2fa"].replace(" ", ""))
        current_code = totp.now()

        otp_input.send_keys(current_code)
        otp_input.send_keys(Keys.RETURN)

        log.info("Fetching mail box...")
        decline_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "declineButton"))
        )
        driver.execute_script("arguments[0].click();", decline_button)
        
        count = 0
        is_failed = False
        while True:
            if count > 15:
                is_failed = True
                break
            if "account.microsoft.com" in driver.current_url:
                break
            time.sleep(1)
            count += 1
        
        if is_failed:
            raise Exception("Unable to fecth mail box :(")

        driver.get("https://outlook.live.com/mail/0/")
        count = 0
        is_failed = False
        while True:
            if count > 15:
                is_failed = True
                break
            if "Inbox" in driver.page_source:
                break
            time.sleep(1)
            count += 1

        if is_failed:
            raise Exception("Unable to check inbox")
        
        other = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-content='Other']"))
        )
        driver.execute_script("arguments[0].click();", other)
        inbox = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[aria-label='Message list']"))
        )
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[aria-label='Message list'] div[role='option']"))
        )
        emails = inbox.find_elements(By.CSS_SELECTOR, "div[role='option']")
        output = []
        for email in emails:
            driver.execute_script("arguments[0].click();", email)
            
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-app-section='MailReadCompose']"))
            )
            subject_element = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-app-section='MailReadCompose'] div[role='heading']"))
            )
            subject = subject_element.text
            body_element = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-app-section='MailReadCompose'] div[role='document']"))
            )
            body = body_element.text
            sender_element = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-app-section='MailReadCompose'] span[aria-label^='From:']"))
            )
            sender = sender_element.text
            output.append({ "subject": subject, "body": body, "sender": sender })

        if not is_found:
            other = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-content='Other']"))
            )
            driver.execute_script("arguments[0].click();", other)

            inbox = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[aria-label='Message list']"))
            )
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[aria-label='Message list'] div[role='option']"))
            )
            emails = inbox.find_elements(By.CSS_SELECTOR, "div[role='option']")

            for email in emails:
                driver.execute_script("arguments[0].click();", email)
                
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-app-section='MailReadCompose']"))
                )
                subject_element = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-app-section='MailReadCompose'] div[role='heading']"))
                )
                subject = subject_element.text
                if "Facebook confirmation code" in subject:
                    is_found = True
                body_element = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-app-section='MailReadCompose'] div[role='document']"))
                )
                body = body_element.text
                sender_element = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-app-section='MailReadCompose'] span[aria-label^='From:']"))
                )
                sender = sender_element.text
                output.append({ "subject": subject, "body": body, "sender": sender })
        return output
    
    def close(self):
        driver.quit()

