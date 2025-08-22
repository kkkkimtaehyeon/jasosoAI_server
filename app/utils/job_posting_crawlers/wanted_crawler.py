from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

from app.utils.job_posting_crawlers.job_posting_crawler_interface import JobPostingCrawlerInterface, selenium_options


class WantedCrawler(JobPostingCrawlerInterface):
    def __init__(self):
        self.driver = webdriver.Chrome(service=Service(), options=selenium_options)

    # 원티드는 모든 채용공고가 동일한 구조를 가지고 있으므로, URL에 따라 크롤링 로직이 달라지지 않습니다.
    # 따라서 llm이 크롤링 결과를 분석할 필요가 없습니다.
    def crawl(self, url: str):
        self.driver.get(url)
        more_button = WebDriverWait(self.driver, 10).until(
            ec.element_to_be_clickable(
                (By.XPATH, '/html/body/div[1]/main/div[1]/div/section/section/article[1]/div/button'))
        )
        # "상세 정보 더 보기" 버튼 클릭
        more_button.click()

        results = {}

        target_element = self.driver.find_element(By.XPATH,
                                                  '/html/body/div[1]/main/div[1]/div/section/header/div/div[1]/a')
        results['company'] = target_element.get_attribute("data-company-name")
        results['position_name'] = target_element.get_attribute("data-position-name")

        target_element = self.driver.find_element(By.XPATH,
                                                  '//*[@id="__next"]/main/div[1]/div/section/header/div/div[1]/span[4]')
        results['experience'] = target_element.text

        target_element = self.driver.find_element(By.XPATH,
                                                  '/html/body/div[1]/main/div[1]/div/section/section/article[1]/div/span/span')
        results['position_detail'] = target_element.text

        # 모든 항목 블록 찾기 (주요업무, 자격요건, 우대사항 등)
        sections = self.driver.find_elements(By.CSS_SELECTOR, 'div.JobDescription_JobDescription__paragraph__87w8I')

        for section in sections:
            try:
                title = section.find_element(By.TAG_NAME, 'h3').text.strip()
                content = section.find_element(By.CSS_SELECTOR, 'span > span').get_attribute('innerHTML')

                # <br> 태그를 줄바꿈으로 치환 (가독성 위해)
                content = content.replace('<br>', '\n').strip()

                results[title] = content
            except Exception as e:
                print(f"오류 발생: {e}")

        # 결과 확인
        # for title, content in results.items():
        #     print(f"[{title}]\n{content}\n")
        # print(" ".join(f"[{title}] {content}" for title, content in results.items()))
        return " ".join(f"[{title}] {content}" for title, content in results.items())