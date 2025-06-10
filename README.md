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
|                            팀장, 아키텍쳐 설계, 개발 환경 구축, 데이터 전처리 및 모델 코드 모듈화, Flask webapp                             |                            Data Pipeline, Airflow                             |                            MLFlow                             |                            Docker, 문서 담당                             |                            Monitoring, 문서 담당                             |

<br>

## 📁 프로젝트 구조 및 설명
```
mlops-cloud-project-mlops_2/
├── dags/                                 # Airflow DAG files
│   └── ...
├── dockerfiles/
│   ├── Dockerfile.experiments           # 개발환경 구성을 위한 Dockerfile
│   └── docker_experiments.sh            # Git clone, Chrome, pip install
├── models/                              # 학습 모델 저장
├── src/
│   ├── assets/                          # 웹 서빙을 위한 리소스
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
├── app.py                         # Flask 웹 애플리케이션
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
- 웹 서비스 데모
![Web-DEMO](https://github.com/AIBootcamp13/mlops-cloud-project-mlops_2/blob/main/images/flask_web_demo.png)

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
- requests, Jinja2
- KaKao Maps API

<br>

## 🛠️ 작품 아키텍처
![MLOps-Architecture](https://github.com/AIBootcamp13/mlops-cloud-project-mlops_2/blob/main/images/mlops-architecture.png)

<br>

## 설치 방법

### 환경 설정
- `cp .env.template .env` # 환경 파일 복제
- `pip install -r requirements.txt` # 필요 패키지 설치

### Docker 실행
- `docker build -t mlops-experiments -f dockerfiles/Dockerfile.experiments .` # Docker 이미지 빌드
- `docker run -it mlops-experiments <github-username>` # 실행 (GitHub 사용자명 포함)

3. Airflow DAG 실행
- `airflow standalone` # DAG: apt_price_prediction 실행

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
- Docker를 활용하여 개발 환경을 통합하고 효율적으로 자원을 관리하는 방법을 직접 체험할 수 있었습니다. 데이터 전처리부터 모델 학습, 추론 API 개발 및 배포까지의 전 과정을 직접 구성하면서 end-to-end MLOps 파이프라인을 구축해볼 수 있었습니다. 이 과정에서 MLOps의 핵심 개념들을 자연스럽게 익힐 수 있었습니다.
### 이진식
- 어려웠다. 좋은 강의와 중간중간 멘토링, 그리고 약 2주의 시간이
있었지만, 도커와 도커 컴포즈를 이용해서 컨테이너를 관리하고
airflow나 mlflow를 이용해서 workflow 관리
하는 것을 익혀서
프로젝트를 완성하는 것은 힘들었다. 개념의 이해도 힘들었고,
개념을 적용시켜 구현을 할때마다 트러블슛 해야할 것들이 생겨서
LLM에게 계속 물어볼 수 밖에 없었다.
### 안재윤
- 모델의 버전별 관리와 실험 관리를 위해 MLflow를 도입하여 Docker
기반의 Tracking 서버 및 모델 레지스트리 환경을 구축하였습니다.
실험 자동 로깅과 모델 버전 관리 파이프라인을 구현하면서, 도구
도입 시 팀 커뮤니케이션과 교육, 그리고 DB/저장소 백엔드 설계의
중요성을 깊이 체감할 수 있었습니다. 특히 팀원들과 실험 관리
프로세스를 표준화하고 협업의 효율성을 높인 경험이 가장 인상 깊게
남았습니다. 추후에는 실시간 서빙 자동화를 도입하여 ML프로젝트의
모든 생애주기에 대한 경험을 확장해나가고 싶습니다.
### 김효석
- Data의 pipeline을 이해하며 배포에 대한 전체적인 흐름을 이해한후  Docker환경에서 Kubernetes와 연계 및  분배하여 모델을 구현하고 Apache Airflow를 통한 Web관리에서 연습해보았습니다. 모델을 진척도나 Best model을 선정 및 검증하며, 스케쥴링하는것을 실습하였다. diagram코딩을 통한 전체적인 pipeline의 계통도를 작성하여 MLops1단계수준의 자동화를 구성해보려고 노력하였습니다. Jenkins 등 다른 프로그램을 구현하지못해 아쉬움이 남았습니다.
### 박진섭
- 이번 프로젝트를 통해 단순한 모델 개발을 넘어, 데이터 수집부터
자동화, 예측 서비스까지 전체 MLOps 파이프라인을 구현해보는
경험을 쌓을 수 있었습니다. 특히 Airflow와 Docker를 활용한
자동화 구성, Hyperopt를 활용한 하이퍼파라미터 튜닝 과정에서
많은 실전 감각을 익혔습니다. 이후에는 MLflow 기반의 실험 추적과
API 확장 등 운영 관점에서의 보완을 해보고 싶습니다.

<br>

