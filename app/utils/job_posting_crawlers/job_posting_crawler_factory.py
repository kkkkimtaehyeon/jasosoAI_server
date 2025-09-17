from typing import Union

from PIL import Image

from app.utils.job_posting_crawlers.job_posting_crawler_interface import JobPostingCrawlerInterface
from app.utils.job_posting_crawlers.wanted_crawler import WantedCrawler
from app.utils.job_posting_crawlers.zighang_crawler import ZighangCrawler

WANTED = 'https://www.wanted.co.kr/'
ZIGHANG = 'https://zighang.com/'
JOBKOREA = 'https://www.jobkorea.co.kr/'
SARMIN = 'https://www.saramin.co.kr/'


class JobPostingCrawlerFactory:
    def __init__(self):
        pass

    # 주어진 채용공고 URL에 따라 적절한 크롤러를 반환합니다.
    @staticmethod
    def get_crawler(job_posting_url: str) -> JobPostingCrawlerInterface:
        if job_posting_url.startswith(WANTED):
            return WantedCrawler()
        elif job_posting_url.startswith(JOBKOREA):
            raise NotImplementedError("Jobkorea crawler is not implemented yet.")
        elif job_posting_url.startswith(SARMIN):
            raise NotImplementedError("Saramin crawler is not implemented yet.")
        elif job_posting_url.startswith(ZIGHANG):
            return ZighangCrawler()
        else:
            raise ValueError("Unsupported job posting URL.")

    def crawl_job_posting(self, job_posting_url: str) -> Union[str, Image]:
        crawler = self.get_crawler(job_posting_url)
        crawled_data = crawler.crawl(job_posting_url)
        return crawled_data


def get_job_posting_crawler_factory():
    return JobPostingCrawlerFactory()
