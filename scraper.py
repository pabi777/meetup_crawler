from selenium import webdriver
from os.path import expanduser
from dbstaffs.db import Dbconnect

class MeetUpScraper:
    def __init__(self):
        self.driver = self.get_new_driver()
        dbconnect=Dbconnect()
        result = dbconnect.query("select xpath_dict from meetup_config where website like 'meetup.com'")
        self.config = result[0][0]
        dbconnect.closeconn()

    def get_new_driver(self):
        PROXY = ["114.5.35.98:38554",] # IP:PORT or HOST:PORT
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--proxy-server=%s' % PROXY)
        home = expanduser("~")
        driver = webdriver.Chrome(f'{home}/chromedriver/chromedriver')#,options=chrome_options)
        return driver


