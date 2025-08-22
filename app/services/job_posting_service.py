from fastapi import Depends

from app.models.job_posting import JobPosting
from app.repositories.job_posting import JobPostingRepository, get_job_posting_repository
from app.services.job_posting_analyze_service import JobPostingAnalyzeService, get_job_posting_analyze_service


class JobPostingService:
    def __init__(self, repo: JobPostingRepository,
                 analyze_service: JobPostingAnalyzeService):
        self.repo = repo
        self.analyze_service = analyze_service

    def get_job_posting(self, job_posting_url: str):
        job_posting = self.repo.find_by_url(job_posting_url)
        if not job_posting:
            # 채용공고 분석
            analyze_result = self.analyze_service.analyze_job_posting(job_posting_url)
            # 채용공고 DB 저장
            job_posting = self.repo.save(JobPosting(
                url=analyze_result.url,
                company_name=analyze_result.company,
                position_title=analyze_result.position_name,
                position_detail=analyze_result.position_detail,
                experience=analyze_result.experience,
                required_qualifications=analyze_result.requirements,
                preferred_qualifications=analyze_result.preferred
            ))
        return job_posting

    def process_job_posting(self, job_posting_url: str):
        pass


def get_job_posting_service(repo: JobPostingRepository = Depends(get_job_posting_repository),
                            analyze_service: JobPostingAnalyzeService = Depends(
                                get_job_posting_analyze_service)) -> JobPostingService:
    return JobPostingService(repo, analyze_service)
