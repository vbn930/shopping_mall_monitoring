from manager import web_driver_manager
from manager import log_manager
from manager import resource_monitor_manager
from crawler import hoopcity_crawler
from crawler import kasina_crawler

import datetime
import json
import time
from discord_webhook import DiscordWebhook, DiscordEmbed

# pyinstaller -n "HOOPCITY_KASINA_MONITORING_PROGRAM_1.5" --clean --onefile main.py

def get_initial_setting_from_config(logger: log_manager.Logger, json_path):
    with open(json_path) as file:
        data = json.load(file)
    
    hoopcity_discord_webhook_url = data["hoopcity_discord_webhook_url"]
    kasina_discord_webhook_url = data["kasina_discord_webhook_url"]
    proxies = data["proxies"]
    wait_time = data["wait_time"]
    
    proxy_objs = []
    for proxy in proxies:
        proxy_info = proxy.split(":")
        proxy_obj = web_driver_manager.Proxy(proxy_info[0], proxy_info[1], proxy_info[2], proxy_info[3])
        proxy_objs.append(proxy_obj)
    
    logger.log_info(f"프로그램 설정을 성공적으로 인식하였습니다. \nHoopcity 디스코드 웹훅 URL : {hoopcity_discord_webhook_url} \nKasina 디스코드 웹훅 URL : {kasina_discord_webhook_url} \n프록시 개수 : {len(proxies)}개 \n모니터링 주기 : {wait_time}분")
    
    return hoopcity_discord_webhook_url, kasina_discord_webhook_url, proxy_objs, wait_time

def run_monitoring(logger: log_manager.Logger, resource_monitor: resource_monitor_manager.ResourceMonitor,
                   driver_manager: web_driver_manager.WebDriverManager, 
                   hoopcity: hoopcity_crawler.HoopcityCrawler, kasina: kasina_crawler.KasinaCrawler, 
                   hoopcity_discord_webhook_url, kasina_discord_webhook_url, proxies):
    
    now = datetime.datetime.now()
    year = f"{now.year}"
    month = "%02d" % now.month
    day = "%02d" % now.day
    hour = "%02d" % now.hour
    minute = "%02d" % now.minute
    
    driver_obj = None
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

    if len(proxies) != 0:
        curr_proxy = proxies.pop(0)
        driver_obj = driver_manager.create_driver(proxy=curr_proxy, user_agent=user_agent)
        proxies.append(curr_proxy)
    else:
        driver_obj = driver_manager.create_driver(user_agent=user_agent)
    
    hoopcity.get_new_items(driver_obj)
    if len(hoopcity.items) != 0:
        hoopcity.save_db_data_as_excel("./DB/Hoopcity", f"{year}{month}{day}{hour}{minute}_Hoopcity")
    
    for new_item in hoopcity.items:
        driver_manager.download_image(img_url=new_item.img_url, img_name="thumbnail", img_path="./TEMP", download_cnt=0)
        webhook = DiscordWebhook(url=hoopcity_discord_webhook_url)
        embed = DiscordEmbed(title=new_item.name, url=new_item.url)
        with open("./TEMP/thumbnail.jpg", "rb") as f:
            webhook.add_file(file=f.read(), filename="thumbnail.jpg")
        embed.set_author(name="HOOPCITY_RESTOCK")
        embed.set_thumbnail(url="attachment://thumbnail.jpg")
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
        embed.set_footer(text="AMNotify KR")
        embed.set_timestamp()
        webhook.add_embed(embed)
        webhook.execute()
        del webhook
        del embed
        time.sleep(1)
    
    hoopcity.clear_data()
    
    kasina.get_new_items(driver_obj)
    if len(kasina.items) != 0:
        kasina.save_db_data_as_excel("./DB/Kasina", f"{year}{month}{day}{hour}{minute}_Kasina")
    
    for new_item in kasina.items:
        driver_manager.download_image(img_url=new_item.img_url, img_name="thumbnail", img_path="./TEMP", download_cnt=0)
        webhook = DiscordWebhook(url=kasina_discord_webhook_url)
        embed = DiscordEmbed(title=new_item.name, url=new_item.url)
        with open("./TEMP/thumbnail.jpg", "rb") as f:
            webhook.add_file(file=f.read(), filename="thumbnail.jpg")
        embed.set_author(name="KASINA_RESTOCK")
        embed.set_thumbnail(url="attachment://thumbnail.jpg")
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
        embed.set_footer(text="AMNotify KR")
        embed.set_timestamp()
        webhook.add_embed(embed)
        webhook.execute()
        del webhook
        del embed
        time.sleep(1)
    
    kasina.clear_data()
    
    driver_manager.delete_driver()
    resource_monitor.print_current_resource_usage()

    logger.save_log()

def run_resource_monitoring(resource_monitor: resource_monitor_manager.ResourceMonitor):
    resource_monitor.print_current_resource_usage()

if __name__ == '__main__':
    # logger = log_manager.Logger(log_manager.LogType.DEBUG)
    # driver_manager = web_driver_manager.WebDriverManager(logger)
    # hoopcity = hoopcity_crawler.HoopcityCrawler(logger)
    # kasina = kasina_crawler.KasinaCrawler(logger)
    # resource_monitor = resource_monitor_manager.ResourceMonitor(logger)
    
    # hoopcity_discord_webhook_url, kasina_discord_webhook_url, proxies, wait_time = get_initial_setting_from_config(logger, "./config/config.json")
    
    # run_monitoring(logger, resource_monitor, driver_manager, hoopcity, kasina, hoopcity_discord_webhook_url, kasina_discord_webhook_url, proxies)
    
    try:
        logger = log_manager.Logger(log_manager.LogType.BUILD)
        driver_manager = web_driver_manager.WebDriverManager(logger)
        hoopcity = hoopcity_crawler.HoopcityCrawler(logger)
        kasina = kasina_crawler.KasinaCrawler(logger)
        resource_monitor = resource_monitor_manager.ResourceMonitor(logger)
        
        hoopcity_discord_webhook_url, kasina_discord_webhook_url, proxies, wait_time = get_initial_setting_from_config(logger, "./config/config.json")
        
        # schedule.every(wait_time).minutes.do(run_monitoring, logger, resource_monitor, driver_manager, hoopcity, kasina, discord_webhook_url, proxies)
        # schedule.every(5).minutes.do(run_resource_monitoring, resource_monitor)
        
        # run_monitoring(logger, resource_monitor, driver_manager, hoopcity, kasina, hoopcity_discord_webhook_url, kasina_discord_webhook_url, proxies)

        while True:
            # schedule.run_pending()
            run_monitoring(logger, resource_monitor, driver_manager, hoopcity, kasina, hoopcity_discord_webhook_url, kasina_discord_webhook_url, proxies)
            logger.log_info(f"다음 정보 신상품 정보 수집까지 {wait_time}분 대기합니다.")
            time.sleep(wait_time*60)
    
    except Exception as e:
        logger.log_error(f"다음과 같은 오류로 프로그램을 종료합니다. : {e}")
        logger.save_log()
    
    logger.log_info(f"프로그램을 종료하시려면 아무 키나 입력해주세요.")
    end = input("")