from abc import abstractmethod, ABC
from selenium.webdriver.chrome.options import Options

# 2. 셀레니움 옵션 설정
selenium_options = Options()
selenium_options.add_argument('--headless')
selenium_options.add_argument('--no-sandbox')
selenium_options.add_argument('--disable-dev-shm-usage')
selenium_options.add_argument("window-size=1920,1080")
selenium_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")


class JobPostingCrawlerInterface(ABC):
    @abstractmethod
    def crawl(self, url: str):
        """
        추상 메서드로, 각 크롤러 클래스에서 구현해야 합니다.
        :return: 크롤링 결과
        """
        pass
