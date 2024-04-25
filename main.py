from manager import web_driver_manager
from manager import log_manager
from crawler import hoopcity_crawler
from crawler import kasina_crawler

logger = log_manager.Logger(log_manager.LogType.DEBUG)
driver_manager = web_driver_manager.WebDriverManager(logger)
hoopcity = hoopcity_crawler.HoopcityCrawler(logger)
kasina = kasina_crawler.KasinaCrawler(logger)

driver = driver_manager.get_driver()
#kasina.get_new_items(driver)
hoopcity.get_new_items(driver)
driver_manager.return_driver(driver)
#kasina.save_db_data_as_excel("./DB/Kasina", "test")
hoopcity.save_db_data_as_excel("./DB/Hoopcity", "test")