import requests
import random
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import pyotp

from util import log


class OneSecMail:
    def generate_email(self):
        self.name = "1secmail"
        domain_list = ['1secmail.com', '1secmail.org', 'rteet.com', '1secmail.net']
        name = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz1234567890', k=10))
        domain = random.choice(domain_list)
        email = f'{name}@{domain}'
        return email, name, domain

    def check_inbox(self, name, domain):
        try:
            url = f"https://www.1secmail.com/api/v1/?action=getMessages&login={name}&domain={domain}"
            response = requests.get(url)
            emails = response.json()
            return emails
        except KeyboardInterrupt:
            pass
        except:
            time.sleep(3)
            return self.check_inbox(name, domain)

    def read_email(self, message_id, name, domain):
        url = f"https://www.1secmail.com/api/v1/?action=readMessage&login={name}&domain={domain}&id={message_id}"
        response = requests.get(url)
        email_content = response.json()
        return email_content


class TempMail:
    def __init__(self):
        self.name = "temp-mail"
        self.session = requests.Session()
        self.domain_list = ["rfcdrive.com", "gonetor.com", "zlorkun.com", "somelora.com", "vvatxiy.com", "dygovil.com",
                       "tidissajiiu.com", "vafyxh.com", "knmcadibav.com", "smykwb.com", "wywnxa.com", "qacmjeq.com",
                       "qejjyl.com", "zvvzuv.com", "bltiwd.com", "qzueos.com", "vwhins.com", "jxpomup.com"]

    def generate_email(self):
        name = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz1234567890', k=10))
        domain = random.choice(self.domain_list)
        email = f'{name}@{domain}'
        r = self.session.post("https://api.internal.temp-mail.io/api/v3/email/new", data={
            "domain": domain,
            "name": name
        })
        email = r.json()["email"]
        nodes = email.split("@")
        return email, nodes[0], nodes[-1]

    # Fetch incoming emails for the generated email
    def check_inbox(self, name, domain):
        try:
            url = f"https://api.internal.temp-mail.io/api/v3/email/{name}@{domain}/messages"
            response = self.session.get(url)
            emails = response.json()
            return emails
        except KeyboardInterrupt:
            pass
        except:
            time.sleep(3)
            return self.check_inbox(name, domain)

    # Fetch the content of a specific email
    def read_email(self, message_id, name, domain):
        url = f"https://api.internal.temp-mail.io/api/v3/email/{name}@{domain}/messages"
        response = self.session.get(url)
        emails = response.json()
        email_content = ""
        for email in emails:
            if email["id"] == message_id:
                email_content = email
                email_content["body"] = email_content["body_html"]
                break
        return email_content



class TenMinuteMail:
    def __init__(self):
        self.name = "temp-mail"
        self.session = requests.Session()
    
    def generate_email(self):
        self.session.get("https://10minutemail.net/new.html")
        r = self.session.get("https://10minutemail.net/address.api.php").json()
        if r["mail_get_host"] == "dcobe.com":
            return self.generate_email()
        return r["mail_get_mail"], r["mail_get_user"], r["mail_get_host"]

    def check_inbox(self, name, domain):
        try:
            r = self.session.get("https://10minutemail.net/address.api.php")
            emails = r.json()["mail_list"]
            # print(emails)
            for email in emails:
                email["id"] = email["mail_id"]
            return emails
        except KeyboardInterrupt:
            pass
        except:
            time.sleep(3)
            return self.check_inbox(name, domain)

    def read_email(self, message_id, name, domain):
        url = f"https://10minutemail.net/mail.api.php?mailid={message_id}"
        response = self.session.get(url).json()
        email_content = {}
        email_content["body"] = response["html"]
        return email_content

