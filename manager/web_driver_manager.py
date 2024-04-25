import undetected_chromedriver as uc 
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium_stealth import stealth
import pyperclip
import subprocess
import time
from datetime import datetime
import requests
import os
import psutil
from dataclasses import dataclass
import random
import zipfile
from manager import log_manager

@dataclass
class Proxy:
    host: str
    port: str
    username: str
    password: str
    
class Driver:
    def __init__(self, logger: log_manager.Logger, driver: WebDriver, proxy: Proxy):
        self.logger = logger
        self.driver = driver
        self.proxy = proxy
        
        driver.maximize_window()
        
    def get_page(self, url, max_wait_time=20):
        is_page_loaded = False
        while(is_page_loaded == False):
            try:
                self.driver.get(url)
                self.driver.implicitly_wait(max_wait_time)
                self.logger.log_debug(f"Get *{url}* page")
                is_page_loaded = True
            except Exception as e:
                self.logger.log_debug(f"Page load failed : {e}")
                is_page_loaded = False
    
    def is_element_exist(self, by, value, element=None):
        is_exist = False
        try:
            if element != None:
                element.find_element(by, value)
            else:
                self.driver.find_element(by, value)
            is_exist = True
        except NoSuchElementException:
            is_exist = False
        return is_exist


class WebDriverManager():
    def __init__(self, logger: log_manager.Logger, proxies=None, is_headless=False, is_udc=False):
        self.logger = logger
        self.driver_list = list()
        if proxies != None:
            for proxy in proxies:
                drive_obj = self.create_driver(proxy, is_headless, is_udc)
                self.driver_list.append(drive_obj)
                #drive_obj.driver.minimize_window()
        else:
            drive_obj = self.create_driver(proxies, is_headless, is_udc)
            self.driver_list.append(drive_obj)
            #drive_obj.driver.minimize_window()
            
    def create_driver(self, user_agent=None, proxy=None, is_headless=False, is_udc=False):
        chrome_options = webdriver.ChromeOptions()
        
        if proxy:
            PROXY_HOST = proxy.host  # rotating proxy or host
            PROXY_PORT = proxy.port # port
            PROXY_USER = proxy.username # username
            PROXY_PASS = proxy.password # password

            manifest_json = """
            {
                "version": "1.0.0",
                "manifest_version": 2,
                "name": "Chrome Proxy",
                "permissions": [
                    "proxy",
                    "tabs",
                    "unlimitedStorage",
                    "storage",
                    "<all_urls>",
                    "webRequest",
                    "webRequestBlocking"
                ],
                "background": {
                    "scripts": ["background.js"]
                },
                "minimum_chrome_version":"22.0.0"
            }
            """

            background_js = """
            var config = {
                    mode: "fixed_servers",
                    rules: {
                    singleProxy: {
                        scheme: "http",
                        host: "%s",
                        port: parseInt(%s)
                    },
                    bypassList: ["localhost"]
                    }
                };

            chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

            function callbackFn(details) {
                return {
                    authCredentials: {
                        username: "%s",
                        password: "%s"
                    }
                };
            }

            chrome.webRequest.onAuthRequired.addListener(
                        callbackFn,
                        {urls: ["<all_urls>"]},
                        ['blocking']
            );
            """ % (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)
        
            pluginfile = './config/proxy_auth_plugin.zip'
            with zipfile.ZipFile(pluginfile, 'w') as zp:
                zp.writestr("manifest.json", manifest_json)
                zp.writestr("background.js", background_js)
            chrome_options.add_extension(pluginfile)
        
        if user_agent:
            chrome_options.add_argument('--user-agent=%s' % user_agent)
        
        if is_headless:
            chrome_options.add_argument('headless')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_experimental_option('excludeSwitches', ['disable-popup-blocking'])
        driver = webdriver.Chrome(options=chrome_options)
        
        return Driver(self.logger, driver, proxy)
    
    #get_driver 후 반드시 사용한 드라이버를 return_driver로 driver manager에 넣어 주어야함
    def get_driver(self):
        curr_driver = self.driver_list.pop(0)
        if curr_driver.proxy:
            self.logger.log_info(f"Current driver ip : {curr_driver.proxy.host}:{curr_driver.proxy.port}")
        return curr_driver
    
    def return_driver(self, driver):
        self.driver_list.append(driver)
        if driver.proxy:
            self.logger.log_info(f"Returned driver ip : {driver.proxy.host}:{driver.proxy.port}")