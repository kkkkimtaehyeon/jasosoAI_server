- ai 자소서 상세 페이지 상단 다음과 같은 정보 출력
  - 회사 키워드 
  - 채용공고 키워드 
  - 자소서 작성 키워드

# TODO
- [x] AI cover letter 생성 횟수 제한 (5)
- [x] 실시간 로그 모니터링 툴 추가
  - sentry로 에러 로그모니터링 + discord 알림 
- [x] cover letter 논리 삭제
- [x] chroma db 영속화
- [x] swagger 암호화
- [x] 개인정보/자소서 데이터 암호화
- [x] 자소서 삭제 시 vector db에서 embedding 삭제
- [ ] api rate limit 고려한 구조 설계
  - L4에서 api rate limit 설정 X -> 사용자의 입력에 따라 api 호출 횟수가 달라짐
  - 일단 DB로 중앙 집중화해서 api 호출 횟수 관리(추상화 신경써서) -> 추후 redis로 변경 고려
- [ ] ai 자소서 최초 생성 시 피드백 요청
- [ ] ai 자소서 항목 재생성 요청
- [ ] user 자소서 업로드 해야하는 이유 설명
- cover_letter_item 테이블에 char_length 컬럼 추가 (tpm 위해서?)
  

# ERROR
- [ ] user 자소서 업로드 시 암호화 되지 않는 문제?



