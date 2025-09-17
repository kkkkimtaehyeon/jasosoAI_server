#FROM python:3.12-slim
#
## 작업 디렉토리 설정
#WORKDIR /app
#
## requirements.txt만 먼저 복사하여 종속성 레이어를 캐시
#COPY requirements.txt .
#
## 파이썬 패키지 설치
## requirements.txt가 변경되지 않는 한 이 단계는 다시 실행되지 않음
#RUN pip install --no-cache-dir -r requirements.txt
#
## 나머지 애플리케이션 파일 복사
## 종속성 설치 후에 복사해야 효율적
#COPY . .
#
## 컨테이너 포트 노출
#EXPOSE 8000
#
## Gunicorn으로 앱 실행
#CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]

FROM python:3.12-slim

# 작업 디렉토리 설정
WORKDIR /app

# ✅ [수정] Chrome 직접 설치로 변경 (의존성 자동 해결)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    --no-install-recommends \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y \
    google-chrome-stable \
    --no-install-recommends \
    # 설치 후 캐시를 삭제하여 이미지 용량을 줄입니다.
    && rm -rf /var/lib/apt/lists/*

# requirements.txt만 먼저 복사하여 종속성 레이어를 캐시
COPY requirements.txt .

# 파이썬 패키지 설치
# requirements.txt가 변경되지 않는 한 이 단계는 다시 실행되지 않음
RUN pip install --no-cache-dir -r requirements.txt

# 나머지 애플리케이션 파일 복사
# 종속성 설치 후에 복사해야 효율적
COPY . .

# 컨테이너 포트 노출
EXPOSE 8000

# Gunicorn으로 앱 실행
CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "120"]