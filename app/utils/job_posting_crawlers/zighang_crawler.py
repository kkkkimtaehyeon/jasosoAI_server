from io import BytesIO

import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from PIL import Image
from selenium.webdriver.support import expected_conditions as ec

from app.utils.job_posting_crawlers.job_posting_crawler_interface import JobPostingCrawlerInterface, selenium_options


class ZighangCrawler(JobPostingCrawlerInterface):
    def __init__(self):
        self.driver = webdriver.Chrome(service=Service(), options=selenium_options)

    def crawl(self, url: str):
        self.driver.get(url)
        image_element = WebDriverWait(self.driver, 10).until(
            ec.presence_of_element_located((By.XPATH, '/html/body/main/div[2]/div[1]/div[1]/div[4]/img'))
        )
        img_path = image_element.get_attribute('src')
        response = requests.get(img_path, )
        if response.status_code != 200:
            raise Exception(f"Failed to fetch image from {img_path}, status code: {response.status_code}")
        return Image.open(BytesIO(response.content))

