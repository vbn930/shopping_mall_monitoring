from manager import web_driver_manager
from manager import log_manager
from crawler import hoopcity_crawler
from crawler import kasina_crawler

import datetime
import schedule
import json
import time
from discord_webhook import DiscordWebhook, DiscordEmbed

def get_initial_setting_from_config(logger: log_manager.Logger, json_path):
    with open(json_path) as file:
        data = json.load(file)
    
    discord_webhook_url = data["discord_webhook_url"]
    proxies = data["proxies"]
    wait_time = data["wait_time"]
    
    proxy_objs = []
    for proxy in proxies:
        proxy_info = proxy.split(":")
        proxy_obj = web_driver_manager.Proxy(proxy_info[0], proxy_info[1], proxy_info[2], proxy_info[3])
        proxy_objs.append(proxy_obj)
    
    logger.log_info(f"설정 정보 받아오기 완료! \n디스코드 웹훅 URL : {discord_webhook_url} \n프록시 개수 : {len(proxies)}개 \n모니터링 주기 : {wait_time}분")
    
    return discord_webhook_url, proxy_objs, wait_time

def run_monitoring(logger: log_manager.Logger, driver_manager: web_driver_manager.WebDriverManager, 
                   hoopcity: hoopcity_crawler.HoopcityCrawler, kasina: kasina_crawler.KasinaCrawler, 
                   discord_webhook_url, proxies):
    
    now = datetime.datetime.now()
    year = f"{now.year}"
    month = "%02d" % now.month
    day = "%02d" % now.day
    hour = "%02d" % now.hour
    minute = "%02d" % now.minute
    
    driver_obj = None
    curr_proxy = proxies.pop(0)
    
    if len(proxies) != 0:
        driver_obj = driver_manager.create_driver(proxy=curr_proxy)
        proxies.append(curr_proxy)
    else:
        driver_obj = driver_manager.create_driver()
    
    hoopcity.get_new_items(driver_obj)
    hoopcity.save_db_data_as_excel("./DB/Hoopcity", f"{year}{month}{day}{hour}{minute}_Hoopcity")
    
    for new_item in hoopcity.items:
        webhook = DiscordWebhook(url=discord_webhook_url)
        embed = DiscordEmbed(title=new_item.name, url=new_item.url)
        embed.set_author(name="HOOPCITY_RESTOCK")
        embed.set_thumbnail(url=new_item.img_url)
        if new_item.discount == "":
            embed.add_embed_field(name="Price", value=new_item.price)
        else:
            embed.add_embed_field(name="Price", value=new_item.price)
            embed.add_embed_field(name="Discount", value=new_item.discount)
        
        size_field_value = ""
        for option in new_item.options:
            option_value = option.size
            
            if option.is_soldout:
                option_value += "[:red_circle:] "
            else:
                option_value += "[:green_circle:] "
            
            size_field_value += option_value
        embed.add_embed_field(name="Size", value=size_field_value)
        webhook.add_embed(embed)
        webhook.execute()
        del webhook
        del embed
        time.sleep(1)
    
    hoopcity.clear_data()
    
    kasina.get_new_items(driver_obj)
    kasina.save_db_data_as_excel("./DB/Kasina", f"{year}{month}{day}{hour}{minute}_Kasina")
    
    for new_item in kasina.items:
        webhook = DiscordWebhook(url=discord_webhook_url)
        embed = DiscordEmbed(title=new_item.name, url=new_item.url)
        embed.set_author(name="KASINA_RESTOCK")
        embed.set_thumbnail(url=new_item.img_url)
        embed.add_embed_field(name="Brand", value=new_item.brand)
        if new_item.discount == "":
            embed.add_embed_field(name="Price", value=new_item.price)
        else:
            embed.add_embed_field(name="Price", value=new_item.price)
            embed.add_embed_field(name="Discount", value=new_item.discount)
        
        size_field_value = ""
        for option in new_item.options:
            option_value = option.size
            
            if option.is_soldout:
                option_value += "[:red_circle:] "
            else:
                option_value += "[:green_circle:] "
            
            size_field_value += option_value
        embed.add_embed_field(name="Size", value=size_field_value)
        webhook.add_embed(embed)
        webhook.execute()
        del webhook
        del embed
        time.sleep(1)
    
    kasina.clear_data()
    
    driver_manager.delete_driver()
    
if __name__ == '__main__':
    logger = log_manager.Logger(log_manager.LogType.DEBUG)
    driver_manager = web_driver_manager.WebDriverManager(logger)
    hoopcity = hoopcity_crawler.HoopcityCrawler(logger)
    kasina = kasina_crawler.KasinaCrawler(logger)
    
    discord_webhook_url, proxies, wait_time = get_initial_setting_from_config(logger, "./config/config.json")
    wait_time = int(wait_time)
    
    run_monitoring(logger, driver_manager, hoopcity, kasina, discord_webhook_url, proxies)