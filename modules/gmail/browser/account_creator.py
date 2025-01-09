#!/usr/bin/env python3
# coding=utf-8

"""
Copyright (c) 2019 mullaihub developers (https://www.mullaihub.com/accng)
See the file 'LICENSE' for copying permission
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import random
import string
import time
import pyotp

from core.module import Module
from util import log
from util.system import terminal_width
from util.colorify import bold
from util.name_generator import random_name


class AccngModule(Module):
    def __init__(self):
        Module.__init__(self)
        self.name = "Gmail Account Creator"
        self.description = "Try to create Gmail accounts and ask you for phone number if needed"
        self.author = ["Jeeva"]
        self.options.add("country", "bangladesh", "Country for names")
        self.options.add("password", "Mullai123@", "Password for Gmail accounts")

    def run(self):
        country = self.options.get("country").lower()
        password = self.options.get("password")

        while True:
            options = uc.ChromeOptions()
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-infobars")
            options.add_argument("--disable-extensions")
            options.add_argument("--profile-directory=Default")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--incognito")
            options.add_argument("--start-maximized")

            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36")

            driver = uc.Chrome(options=options)
            driver.get("https://accounts.google.com/signup")

            first_name, last_name = random_name(country)

            # page 1
            first_name_input = WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located((By.NAME, "firstName"))
            )
            first_name_input.send_keys(first_name)

            last_name_input = WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located((By.NAME, "lastName"))
            )
            last_name_input.send_keys(last_name)

            time.sleep(1)
            driver.find_element(By.CSS_SELECTOR, "button").click()

            # page 2
            month_select = WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located((By.ID, "month"))
            )
            Select(month_select).select_by_value(f"{random.randint(1, 12)}")

            day_input = WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located((By.ID, "day"))
            )
            day_input.send_keys(f"{random.randint(1, 29)}")

            year_input = WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located((By.ID, "year"))
            )
            year_input.send_keys(f"{random.randint(1985, 2005)}")

            gender_select = WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located((By.ID, "gender"))
            )
            Select(gender_select).select_by_value(f"{random.randint(1, 2)}")

            time.sleep(1)
            driver.find_element(By.CSS_SELECTOR, "button").click()
            
            email_name = self.generate_random_email(first_name, last_name)
            log.info(f"e-Mail: {email_name}@gmail.com")
            username_input = WebDriverWait(driver, 30).until(
                EC.any_of(
                    EC.visibility_of_element_located((By.NAME, "Username")),
                    EC.visibility_of_element_located((By.ID, "selectionc4")),
                )
            )
            if "Create your own Gmail address" in driver.page_source:
                time.sleep(1)
                username_input.click()
                time.sleep(1)
                username_input = driver.find_element(By.NAME, "Username")

            username_input.send_keys(email_name)
            time.sleep(1)
            driver.find_element(By.CSS_SELECTOR, "button").click()
            
            # page 3
            pass_input = WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located((By.NAME, "Passwd"))
            )
            pass_input.send_keys(password)
            driver.find_element(By.NAME, "PasswdAgain").send_keys(password)
            time.sleep(1)
            driver.find_element(By.CSS_SELECTOR, "button").click()

            # page 4
            element = WebDriverWait(driver, 30).until(
                EC.any_of(
                    EC.visibility_of_element_located((By.ID, "phoneNumberId")),
                )
            )
            if "Get a verification code sent to your phone" in driver.page_source:
                log.info("Waiting for phone number... press enter after done")
                input()
            else:
                log.info("TODO: handle if no phone number was asked")
                input()

            driver.get("https://myaccount.google.com/security?utm_source=sign_in_no_continue")
            auth_element = WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "a[href*='authenticator']"))
            )
            time.sleep(1)
            auth_element.click()
            WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "a[href*='play.google.com']"))
            )
            time.sleep(1)
            driver.execute_script("""Array.from(document.querySelectorAll("span")).find(el => el.textContent.trim() == "Set up authenticator").click();""")
            self.wait_for_text(driver, ["Scan a QR code"])
            time.sleep(5)
            time.sleep(1)
            driver.execute_script("""Array.from(document.querySelectorAll("span")).find(el => el.textContent.trim() == "Can’t scan it?").click();""")
            time.sleep(1)
            twofa_token = driver.execute_script("""return Array.from(document.querySelectorAll("strong")).find(el => el.textContent.trim().split(" ").length == 8).textContent.trim();""")
            log.info(f"2FA Token: {twofa_token}")
            time.sleep(1)
            driver.execute_script("""Array.from(document.querySelectorAll("span")).find(el => el.textContent.trim() == "Next").click();""")
            code_input = WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "input[placeholder='Enter Code']"))
            )
            totp = pyotp.TOTP(twofa_token.replace(" ", ""))
            current_code = totp.now()
            code_input.send_keys(current_code)
            time.sleep(1)
            driver.execute_script("""Array.from(document.querySelectorAll("span")).find(el => el.textContent.trim() == "Verify").click();""")

            twofa_btn = WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "a[href='embedded/signinoptions/two-step-verification']"))
            )
            time.sleep(1)
            twofa_btn.click()
            twofa_btn = WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "button[aria-label='Turn on 2-Step Verification']"))
            )
            time.sleep(1)
            twofa_btn.click()
            self.wait_for_text(driver, ["Skip"])
            time.sleep(1)
            driver.execute_script("""Array.from(document.querySelectorAll("span")).find(el => el.textContent.trim() == "Skip").click();""")
            self.wait_for_text(driver, ["Continue anyway"])
            time.sleep(1)
            driver.execute_script("""Array.from(document.querySelectorAll("span")).find(el => el.textContent.trim() == "Continue anyway").click();""")
            self.wait_for_text(driver, ["now protected with 2-Step Verification"])
            
            print("-" * terminal_width())
            log.success(f"e-Mail: {bold(email_name+"@gmail.com")}")
            log.success(f"Password: {bold(password)}")
            log.success(f"2FA: {bold(twofa_token)}")
            print("-" * terminal_width())
            with open(f"gmail_accounts.txt", "a") as f:
                f.write(f"{email_name+"@gmail.com"}|{password}|{twofa_token}\n")
            driver.quit()

    def wait_for_text(self, driver, texts):
        while True:
            is_found = False
            for text in texts:
                if text in driver.page_source:
                    is_found = True
                    break
            if is_found:
                break
            time.sleep(1)

    def generate_random_email(self, first_name, last_name):
        first_name = first_name.lower().strip()
        last_name = last_name.lower().strip()

        # List of possible email domains

        # Generate a random number or string to append
        random_number = random.randint(1, 9999)
        random_string = ''.join(random.choices(string.ascii_lowercase, k=3))

        # Combine to create a unique email address
        email = f"{first_name}.{last_name}{random_number}{random_string}"

        # Alternatively, add a random string instead of a number
        # email = f"{first_name}.{last_name}{random_string}@{random.choice(domains)}"

        return email

