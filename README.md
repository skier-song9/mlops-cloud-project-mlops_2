# 아파트 가격 예측 MLOps 프로젝트
복잡한 데이터 수집에서 트랙코드, 모델통화, 학습, 실적 예측, 구조 안내 까지 하는 end-to-end MLOps 구조를 구현한 프로젝트입니다.
<br>

## 💻 프로젝트 개요
이 프로젝트는 실제 부동산 거래 데이터를 기반으로 머신러닝 모델을 통해 서울시 아파트 가격을 예측하는 end-to-end MLOps 파이프라인입니다. 데이터 수집부터 전처리, 모델 학습, 평가, 예측, 자동화, 배포까지 모든 단계가 통합되어 있습니다.

- 가장 많이 구성되는 시공지역(서울)의 아파트 실거래가 데이터를 API를 통해 수집
- 데이터 전처리, 모델 학습, 평가 및 예측 결과를 Flask 웹 애플리케이션으로 제공
- MLOps의 전형적인 구조를 기반으로 구현 (Airflow, MLflow, AWS S3, Docker, CatBoost/LGBM, Hyperopt)

<br>

## 👨‍👩‍👦‍👦 팀 구성원

| ![송규헌](https://avatars.githubusercontent.com/u/113088511?v=4) | ![이진식](https://avatars.githubusercontent.com/u/57533441?v=4) | ![안재윤](https://avatars.githubusercontent.com/u/204634763?v=4) | ![김효석](https://avatars.githubusercontent.com/u/159979869?v=4) | ![박진섭](https://avatars.githubusercontent.com/u/208775216?s=400&v=4) |
| :--------------------------------------------------------------: | :--------------------------------------------------------------: | :--------------------------------------------------------------: | :--------------------------------------------------------------: | :--------------------------------------------------------------: |
|            [송규헌](https://github.com/skier-song9)             |            [이진식](https://github.com/hoppure)             |            [안재윤](https://github.com/Skylar-Ahn)             |            [김효석](https://github.com/david1005910)             |            [박진섭](https://github.com/seob1504)             |
|                            팀장, 담당 역할                             |                            담당 역할                             |                            담당 역할                             |                            담당 역할                             |                            담당 역할                             |

<br>

## 📁 프로젝트 구조 및 설명
```
mlops-cloud-project-mlops_2/
├── dags/
│   └── allprocessv2.py                  # Airflow DAG
├── dockerfiles/
│   ├── Dockerfile.experiments           # Dockerfile
│   └── docker_experiments.sh            # Git clone, Chrome, pip install
├── models/                              # 학습 모델 저장
├── src/
│   ├── assets/                          # index.html
│   ├── dataset/
│   │   ├── getdatav2.py                 # 국토교통부 API 데이터 수집
│   │   ├── data_loader.py              # S3에서 데이터 로딩
│   │   ├── data_process.py             # 데이터 전처리
│   │   └── data_geoprocess.py          # 위치정보 병합 등 지오 프로세싱
│   ├── evaluate/
│   │   └── evaluate.py                 # 모델 평가
│   ├── inference/
│   │   └── inference.py                # 추론 기능
│   ├── model/
│   │   ├── model_cards.py              # 모델 래퍼
│   │   └── hyperparam_tuning.py        # 하이퍼파라미터 튜닝
│   ├── utils/
│   │   ├── utils.py                    # 경로, seed, 시각화 유틸리티
│   │   └── constant.py                 # Enum 및 상수 정의
├── main.py
├── webapp.py                            # Flask 웹 애플리케이션
├── requirements.txt
├── .env.template
├── .gitignore
```
<br>

## 프로젝트 구조 및 설명
### Airflow DAG (allprocessv2.py)
- get_data: API로 데이터 수집 및 저장
- preprocess_data: 전처리 및 CatBoost/LGBM을 통한 학습 후 모델 저장
### 데이터 파이프라인
- getdatav2.py: 국토부 API를 통해 거래 데이터 수집 후 S3에 저장
- data_loader.py: S3에서 CSV 다운로드
- data_process.py: 전처리, 인코딩, 위치정보 병합
- data_geoprocess.py: 주소 및 좌표 기반의 지오코딩 처리
### 모델 학습 및 평가
- model_cards.py: LGBM, CatBoost 래퍼 구성
- evaluate.py: RMSE 기반 Cross Validation
- hyperparam_tuning.py: Hyperopt 기반 하이퍼파라미터 튜닝
### 추론 및 서빙
- inference.py: 모델 로드, 추론 로직 포함
- webapp.py: Flask 웹 서버 및 시각화 지원

<br>

## 💻​ 구현 기능
### 실거래가 데이터 수집 자동화
- 국토교통부 API를 활용하여 서울시의 아파트 실거래가 데이터를 수집하고 저장합니다.
### 데이터 전처리 및 통합
- 주소, 좌표, 구조화된 특성 정보 등 외부 데이터를 결합하고 정제합니다.
### 모델 학습 및 튜닝
- CatBoost, LightGBM 기반 모델을 학습하고, Hyperopt로 하이퍼파라미터를 최적화합니다.
### 모델 평가 및 저장
- RMSE 기반 교차검증을 수행하고 모델을 저장합니다.
### 예측 및 추론 기능 제공
- 학습된 모델을 기반으로 아파트 가격 예측 결과를 제공합니다.
### 웹 서비스 구현
- 웹 서비스 구현: Flask로 간단한 예측 서비스 웹 애플리케이션을 제공합니다.
### 워크플로우 자동화
- Apache Airflow를 통해 전체 프로세스를 스케줄링 및 자동화합니다.
### 환경 재현 및 이식성
- Docker 환경을 통해 운영체제에 무관하게 일관된 실행 환경을 제공합니다.

<br>

## 🔨 개발 환경 및 기술 스택
### 개발 도구
- 주 언어 : python 3.11
- 버전 및 이슈관리 : Github
- 협업 툴 : Github, Notion

### ML/AI 스택
- LightGBM (4.6.0)
- CatBoost (1.2.7)
- scikit-learn (1.6.1)
- Hyperopt (0.2.7)
- category_encoders (2.8.1)
-  pandas, numpy, shap, shapely, joblib, geopandas

### MLOps 인프라
- Apache Airflow (3.0.1)
- AWS S3 + s3fs
- python-dotenv
- tqdm, fire, xmltodict

### 웹 서비스
- Flask (3.1.0)
- Flask-CORS
- selenium (4.33.0)
- folium, requests, Jinja2

<br>

## 🛠️ 작품 아키텍처(필수X)
- #### _아래 이미지는 예시입니다_
![이미지 설명](https://miro.medium.com/v2/resize:fit:4800/format:webp/1*ub_u88a4MB5Uj-9Eb60VNA.jpeg)

<br>

## 설치 방법

### 환경 설정
- cp .env.template .env # 환경 파일 복제
- pip install -r requirements.txt # 필요 패키지 설치

### Docker 실행
- docker build -t mlops-experiments -f dockerfiles/Dockerfile.experiments . # Docker 이미지 빌드
- docker run -it mlops-experiments <github-username> # 실행 (GitHub 사용자명 포함)

3. Airflow DAG 실행
- airflow standalone # DAG: apt_price_prediction 실행

<br>

## 핵심 가치
- 현실 데이터 기반 학습: 국토교통부 공공 API를 통한 실제 부동산 거래 데이터를 사용하여 모델의 신뢰성과 적용 가능성 향상
- MLOps 통합 설계: 데이터 수집부터 배포까지 전 과정을 자동화하여 재현 가능하고 운영 가능한 구조 확보
- 모듈화된 코드 구조: 각 단계가 명확히 구분되어 있어 유지보수 및 확장성 우수
- 자동화 및 스케줄링: Airflow를 통한 작업 스케줄링으로 운영 효율성 향상
- 확장 가능한 웹 서비스: Flask를 통한 예측 결과 제공, 추후 Streamlit/FastAPI로 확장 가능

<br>

## 📌 프로젝트 회고
### 송규헌
- _프로젝트 회고를 작성해주세요_
### 이진식
- _프로젝트 회고를 작성해주세요_
### 안재윤
- _프로젝트 회고를 작성해주세요_
### 김효석
- _프로젝트 회고를 작성해주세요_
### 박진섭
- _프로젝트 회고를 작성해주세요_

<br>

## 📰​ 참고자료
- _참고자료를 첨부해주세요_
