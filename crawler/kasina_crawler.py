from dataclasses import dataclass
from manager import file_manager
from manager import web_driver_manager
import json
import pandas as pd
import time

from selenium.webdriver.common.by import By

@dataclass
class Option:
    size: str
    is_soldout: bool

@dataclass
class KasinaItem:
    name: str
    brand: str
    price: str
    discount: str
    img_url: str
    url: str
    options: list

class KasinaCrawler:
    def __init__(self, logger):
        self.logger = logger
        self.file_manager = file_manager.FileManager()
        self.database = dict()
        self.items = list()
        
        self.database_init()
        self.file_manager.create_dir("./DB/Kasina")
        
    def clear_data(self):
        self.database_init()
        self.items.clear()
    
    def database_init(self):
        self.database.clear()
        self.database["BRAND"] = list()
        self.database["NAME"] = list()
        self.database["PRICE"] = list()
        self.database["DISCOUNT"] = list()
        self.database["SIZE"] = list()
        self.database["IMAGE"] = list()
        self.database["URL"] = list()
        
    def add_item_to_database(self, item: KasinaItem):
        self.database["BRAND"].append(item.brand)
        self.database["NAME"].append(item.name)
        self.database["PRICE"].append(item.price)
        self.database["DISCOUNT"].append(item.discount)
        
        size_str = ""
        for option in item.options:
            text = option.size
            if option.is_soldout:
                text += "(품절)"

            size_str += text
            if option.size != item.options[-1].size:
                size_str += ", "
        
        self.database["SIZE"].append(size_str)
        self.database["IMAGE"].append(item.img_url)
        self.database["URL"].append(item.url)
        
    def get_latest_item(self, json_path):
        with open(json_path) as file:
            data = json.load(file)
            
        latest_item_url = data["kasina"]
        
        return latest_item_url
    
    def set_latest_item(self, json_path, latest_item_url):
        pass
    
    def get_last_page(self, driver_obj: web_driver_manager.Driver):
        driver = driver_obj.driver
        
        if driver_obj.is_element_exist(By.CLASS_NAME, "btn_page.btn_page_last"):
            last_page_btn = driver.find_element(By.CLASS_NAME, "btn_page.btn_page_last")
            last_page_btn.click()
            driver.implicitly_wait(30)
        
        last_page = driver.find_element(By.CLASS_NAME, "pagination").find_elements(By.TAG_NAME, "li")[-1].text
        
        return int(last_page)
    
    def close_popup(self, driver_obj: web_driver_manager.Driver):
        driver = driver_obj.driver
        
        btn_elements = driver.find_elements(By.TAG_NAME, "button")
        
        for btn_element in btn_elements:
            if btn_element.get_attribute("color") == "bgtxt-absolute-white-dark":
                btn_element.click()
                print("popup closed")
                break
        
    def find_items_in_list(self, driver_obj: web_driver_manager.Driver, latest_item_url):
        url = "https://www.kasina.co.kr/new?sortType=RECENT_PRODUCT"
        items = []
        driver = driver_obj.driver
        
        driver_obj.get_page(url)
        
        last_page = 1
        
        print(f"Last page : {last_page}")
        
        for i in range(1, last_page+1):
            page_url = f"https://www.kasina.co.kr/new?sortType=RECENT_PRODUCT&page={i}"
            
            driver_obj.get_page(page_url)
            
            time.sleep(10)
            
            # SCROLL_PAUSE_TIME = 0.5

            # # Get scroll height
            # last_height = driver.execute_script("return document.body.scrollHeight")

            # while True:
            #     # Scroll down to bottom
            #     driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            #     # Wait to load page
            #     time.sleep(SCROLL_PAUSE_TIME)

            #     # Calculate new scroll height and compare with last scroll height
            #     new_height = driver.execute_script("return document.body.scrollHeight")
            #     if new_height == last_height:
            #         break
            #     last_height = new_height
            
            item_elements = driver.find_elements(By.CLASS_NAME, "l-grid__col.l-grid__col--6")
            
            for item_element in item_elements:
                item_url = item_element.find_element(By.CLASS_NAME, "c-card__link").get_attribute("href")
                
                if latest_item_url != item_url:
                    item_img_url = item_element.find_element(By.CLASS_NAME, "c-lazyload.c-lazyload--ratio_1x1.c-lazyload--gray").find_element(By.TAG_NAME, "img").get_attribute("src").split("?")[0]
                    item_name = item_element.find_element(By.CLASS_NAME, "c-card__name").find_element(By.TAG_NAME, "dd").text
                    item_brand = item_element.find_element(By.CLASS_NAME, "c-card__brand").find_element(By.TAG_NAME, "span").text
                    item_price_element = item_element.find_element(By.CLASS_NAME, "c-card__price")
                    item_price = ""
                    item_discount = ""
                    if driver_obj.is_element_exist(By.TAG_NAME, "del", item_price_element):
                        item_price = item_price_element.find_element(By.TAG_NAME, "del").text
                        item_discount = item_price_element.find_element(By.TAG_NAME, "strong").text
                    else:
                        item_price = item_price_element.find_element(By.TAG_NAME, "strong").text
                    
                    item = KasinaItem(name=item_name, brand=item_brand, price=item_price, discount=item_discount, img_url=item_img_url, url=item_url, options=[])
                    print(item)
                    items.append(item)
                else:
                    return items
        
        return items
    
    def get_item_option(self, driver_obj: web_driver_manager.Driver, item_url):
        driver = driver_obj.driver
        driver_obj.get_page(item_url)
        options = []
        if driver_obj.is_element_exist(By.CLASS_NAME, "c-chip-input"):
            option_elements = driver.find_element(By.CLASS_NAME, "c-chip-input").find_elements(By.TAG_NAME, "input")
            for option_element in option_elements:
                option_text = option_element.get_attribute("id")
                option_soldout = not option_element.is_enabled()
                option = Option(size=option_text, is_soldout=option_soldout)
                options.append(option)
        return options
    
    def get_new_items(self, driver_obj: web_driver_manager.Driver):
        json_path = ".\config\latest_item_info.json"
        latest_item_url = self.get_latest_item(json_path)
        print(f"Last item url : {latest_item_url}")
        new_items = self.find_items_in_list(driver_obj, latest_item_url)
        self.items += new_items
        if len(new_items) != 0:
            self.set_latest_item(json_path, new_items[0].url)
            
        for i in range(len(self.items)):
            item_option = self.get_item_option(driver_obj, self.items[i].url)
            self.items[i].options = item_option
            print(self.items[i])
            self.add_item_to_database(self.items[i])
            
    def save_db_data_as_excel(self, save_path, file_name):
        data_frame = pd.DataFrame(self.database)
        data_frame.to_excel(f"{save_path}/{file_name}.xlsx", index=False)