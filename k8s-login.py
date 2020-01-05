#!/usr/bin/env python3
import os
import sys
import subprocess
from getpass import getpass
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium import webdriver

environment = input('Environment: ')
myuser = getpass('Username: ')
mypassword = getpass('Password: ')

# chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
browser = Chrome(options=chrome_options)

# login to gangway
browser.get('https://gangway.' + environment + '.example.com/')
button = browser.find_elements_by_xpath(
    "//a[@href='/login']")[0]
button.click()

username = browser.find_element_by_id("login")
password = browser.find_element_by_id("password")
username.send_keys(myuser)
password.send_keys(mypassword)
browser.find_element_by_id("submit-login").click()

# get stuff from dex
cert = browser.find_element_by_xpath(
    "(//span[@class='token string'])[position()=1]")
client_secret = browser.find_element_by_xpath(
    "(//span[@class='token string'])[position()=4]")
refresh_token = browser.find_element_by_xpath(
    "(//span[@class='token string'])[position()=5]")
id_token = browser.find_element_by_xpath(
    "(//span[@class='token string'])[position()=6]")

# write certificate file
ca = open("ca-k8s." + environment + ".example.com.pem", "w")
ca.write(str(cert.text).replace('"', '') + "\n")
ca.close()

# set-cluster
os.system("kubectl config set-cluster k8s." + environment + ".example.com --server=https://api.k8s." +
          environment + ".example.com --certificate-authority=ca-k8s." +
          environment + ".example.com.pem --embed-certs")

# set-credentials
os.system("kubectl config set-credentials" + myuser + "@k8s." + environment + ".example.com  \
    --auth-provider=oidc  \
    --auth-provider-arg='idp-issuer-url=https://dex." + environment + ".example.com/dex'  \
    --auth-provider-arg='client-id=" + environment + "-gangway'  \
    --auth-provider-arg=" + client_secret.text + " \
    --auth-provider-arg=" + refresh_token.text + " \
    --auth-provider-arg=" + id_token.text + "")

# set-context
os.system("kubectl config set-context k8s." + environment + ".example.com --cluster=k8s." +
          environment + ".example.com --user=" + myuser + "@k8s." + environment + ".example.com")

# use-context
os.system("kubectl config use-context k8s." + environment + ".example.com")

# delete certificate
os.remove("ca-k8s." + environment + ".example.com.pem")
