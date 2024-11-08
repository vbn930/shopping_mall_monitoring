from dataclasses import dataclass
from manager import file_manager
from manager import web_driver_manager
from manager import log_manager
import json
import pandas as pd
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
    def __init__(self, logger: log_manager.Logger):
        self.logger = logger
        self.file_manager = file_manager.FileManager()
        self.database = dict()
        self.items = list()
        
        self.database_init()
        self.file_manager.create_dir("./DB/Kasina")
        self.file_manager.create_dir("./TEMP")
        
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
    
    def options_to_list(self, options: list):
        option_list = []
        for option in options:
            val = []
            val.append(option.size)
            val.append(option.is_soldout)
            option_list.append(val)
        
        return option_list

    def list_to_options(self, option_list: list):
        options = []
        for option in option_list:
            val = Option(option[0], option[1])
            options.append(val)

        return options
    
    def add_items_to_restock_check_list(self):
        json_path = "./config/restock_check_list.json"
        with open(json_path, encoding='UTF-8') as file:
            data = json.load(file)
        
        restock_check_list = data["kasina"]
        for item in self.items:
            restock_check_list.append([item.name, item.brand, item.img_url, item.url, False, self.options_to_list(item.options)])
            
        data["kasina"] = restock_check_list
        
        with open(json_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent="\t", ensure_ascii=False)
    
    def get_restock_check_items(self):
        json_path = "./config/restock_check_list.json"
        with open(json_path, encoding='UTF-8') as file:
            data = json.load(file)

        restock_check_list = data["kasina"]
        restock_list = []
        restock_check = []
        for item in restock_check_list:
            restock_check.append(item[4])
            restock_item = KasinaItem(name=item[0], brand=item[1], price="", discount="", img_url=item[2], url=item[3], options=self.list_to_options(item[5]))
            restock_list.append(restock_item)
                
        return restock_list, restock_check
    
    def update_restock_check_items(self, items, restock_check):
        json_path = "./config/restock_check_list.json"
        with open(json_path, encoding='UTF-8') as file:
            data = json.load(file)
            
        restock_check_list = []

        for i in range(len(items)):
            item = items[i]
            restock_check_list.append([item.name, item.brand, item.img_url, item.url, restock_check[i],  self.options_to_list(item.options)])
            
        data["kasina"] = restock_check_list
        
        with open(json_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent="\t", ensure_ascii=False)
            
        self.logger.log_debug(f"Kasina 재입고 알림 제품 업데이트 완료.")
    
    def set_latest_item(self, json_path, latest_item_url):
        with open(json_path) as file:
            data = json.load(file)
            
        data["kasina"] = latest_item_url
        
        with open(json_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent="\t")
            
    def get_last_page(self, driver_obj: web_driver_manager.Driver):
        url = "https://www.kasina.co.kr/new"
        driver = driver_obj.driver
        driver_obj.get_page(url)
        
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="cts"]/div/div[2]/div/div[1]/strong')))
        
        total_item = int(driver.find_element(By.XPATH, '//*[@id="cts"]/div/div[2]/div/div[1]/strong').text.replace(",",""))
        last_page = total_item // 100
        remain = total_item % 100
        if remain != 0:
            last_page += 1
        
        self.logger.log_debug(f"Kasina : Total {last_page} of pages ")

        return last_page
        
    def find_items_in_list(self, driver_obj: web_driver_manager.Driver, latest_item_url):
        items = []
        driver = driver_obj.driver
        
        last_page = self.get_last_page(driver_obj)
        
        for i in range(1, last_page+1):
            page_url = f"https://www.kasina.co.kr/new?page={i}"
            
            driver_obj.get_page(page_url)
            
            time.sleep(10)
            
            if i == 1:
                # For clearing popup window
                actions = ActionChains(driver)
                actions.key_down(Keys.ESCAPE).key_up(Keys.ESCAPE).perform()
            
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "l-grid__col.l-grid__col--6")))
            
            item_elements = driver.find_elements(By.CLASS_NAME, "l-grid__col.l-grid__col--6")
            for item_element in item_elements:
                item_url = item_element.find_element(By.CLASS_NAME, "c-card__link").get_attribute("href")
                if latest_item_url != item_url:
                    item_img_url = item_element.find_element(By.CLASS_NAME, "c-lazyload.c-lazyload--ratio_1x1.c-lazyload--gray").find_element(By.TAG_NAME, "img").get_attribute("src").split("?")[0]
                    item_name = item_element.find_element(By.CLASS_NAME, "c-card__name").find_element(By.TAG_NAME, "dd").text
                    item_brand = item_element.find_element(By.CLASS_NAME, "c-card__brand").find_element(By.TAG_NAME, "span").text
                    item_price = ""
                    item_discount = ""
                    
                    item = KasinaItem(name=item_name, brand=item_brand, price=item_price, discount=item_discount, img_url=item_img_url, url=item_url, options=[])
                    items.append(item)
                else:
                    return items
        return items
    
    def get_item_detail_info(self, driver_obj: web_driver_manager.Driver, item_url):
        driver = driver_obj.driver
        driver_obj.get_page(item_url)
        options = []
        
        item_price = ""
        item_discount = ""
        
        if driver_obj.is_element_exist(By.CLASS_NAME, "dtl-price__origin"):
            item_price = driver.find_element(By.XPATH, '//*[@id="cts"]/div/div[1]/div[2]/div/div[1]/div[3]/dl/div[1]/dd/del').text
            item_discount = driver.find_element(By.XPATH, '//*[@id="cts"]/div/div[1]/div[2]/div/div[1]/div[3]/dl/div[2]/dd/strong[2]').text
        else:
            item_price = driver.find_element(By.CLASS_NAME, 'dtl-price__discount').find_element(By.TAG_NAME, "strong").text

        if driver_obj.is_element_exist(By.CLASS_NAME, "c-chip-input"):
            option_elements = driver.find_element(By.CLASS_NAME, "c-chip-input").find_elements(By.TAG_NAME, "input")
            for option_element in option_elements:
                option_text = option_element.get_attribute("id")
                option_soldout = not option_element.is_enabled()
                option = Option(size=option_text, is_soldout=option_soldout)
                options.append(option)
        return options, item_price, item_discount
    
    def get_new_items(self, driver_obj: web_driver_manager.Driver):
        json_path = ".\config\latest_item_info.json"
        latest_item_url = self.get_latest_item(json_path)
        new_items = self.find_items_in_list(driver_obj, latest_item_url)
        self.items += new_items
        if len(new_items) != 0:
            self.set_latest_item(json_path, new_items[0].url)
        
        self.logger.log_info(f"Kasina : 총 {len(self.items)}개의 신상품을 발견 하였습니다.")
        
        for i in range(len(self.items)):
            item_option, item_price, item_discount = self.get_item_detail_info(driver_obj, self.items[i].url)
            self.items[i].options = item_option
            self.items[i].price = item_price
            self.items[i].discount = item_discount
            self.logger.log_info(f"신상품 {self.items[i].name}의 정보 수집을 완료하였습니다.")
            self.add_item_to_database(self.items[i])
        
        self.add_items_to_restock_check_list()
        restock_item_list, restock_check = self.get_restock_check_items()
        self.logger.log_info(f"Kasina : 총 {restock_check.count(True)}개의 재고 확인 상품을 발견 하였습니다.")
        for i in range(len(restock_item_list)):
            if restock_check[i] == True:
                restock_item = restock_item_list[i]
                item_option, item_price, item_discount = self.get_item_detail_info(driver_obj, restock_item.url)
                if restock_item.options != item_option:
                    restock_item.options = item_option
                    restock_item.price = item_price
                    restock_item.discount = item_discount
                    self.logger.log_info(f"재고 확인 상품 {restock_item.name}의 정보 수집을 완료하였습니다.")
                    self.add_item_to_database(restock_item)
                    self.items.append(restock_item)
                else:
                    self.logger.log_info(f"재고 확인 상품 {restock_item.name}의 정보 변경 사항이 없습니다.")
        
        if len(restock_item_list) != 0:
            self.update_restock_check_items(restock_item_list, restock_check)
                
    def save_db_data_as_excel(self, save_path, file_name):
        data_frame = pd.DataFrame(self.database)
        data_frame.to_excel(f"{save_path}/{file_name}.xlsx", index=False)