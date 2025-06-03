import os
import zipfile
import time
import io
import pandas as pd
from dotenv import load_dotenv
import gc

from selenium import webdriver 
from selenium.webdriver.common.by import By # 위치 지정자(css셀렉터,xpath,id 등)를 위한 클래스
from selenium.webdriver.common.keys import Keys # 키보드 키값이 정의된 클래스
from selenium.common.exceptions import TimeoutException,NoSuchElementException # 요소를 못 찾을 경우 예외처리용
from selenium.webdriver.support import expected_conditions as EC # Explicit Wait 사용 시
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from geopy.geocoders import Nominatim
import re
from tqdm import tqdm

import requests
import xmltodict

import sys
sys.path.append(
    os.path.dirname(os.path.dirname( # /mlops/
        os.path.dirname(  # /mlops/src
            os.path.abspath(__file__)  # /mlops/src/dataset
        )
    ))
)
from src.utils.utils import project_path, get_current_time, download_dir

def get_driver():
    options = Options()
    options.add_experimental_option('detach',True)
    options.add_argument('--lang=ko-KR') # set region as US
    # ====== 🔔 크롬에서 "권한허용" 확인창이 뜨는 경우 🔔 ======
    # 웹드라이버 생성 시 options키워드 인수로 추가옵션을 설정해야 한다.
    # 크롬의 경우 1이 허용, 2가 차단
    options.add_experimental_option("prefs", {"profile.default_content_setting_values.notifications": 1})
    # ======================================================
    # 기타 안정성 옵션 추가
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # 사용자 검색자료 다운로드
    options.add_experimental_option("prefs", {
        "download.default_directory": download_dir(),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })
    
    options.add_argument('--headless=new') # 창을 띄우지 않고 실행
    driver = webdriver.Chrome(
        options=options
    )
    # resize the window size
    driver.set_window_size(width=1280 , height=960)
    return driver


def download_umdCd():
    """ download code information excel file from S3 storage.
    :return dictionary: key=code, value=text
    """
    data_path = os.path.join(project_path(), 'src', 'data', 'umdCd.xls')
    # download data file from s3
    load_dotenv(dotenv_path=os.path.join(project_path(), '.env'))
    url = os.getenv('S3_URL_UMDCD')
    try:
        # Download the file from the URL
        response = requests.get(url)
        response.raise_for_status()  # Raise an error if download fails
        # Save file
        with open(data_path, 'wb') as f:
            f.write(response.content)
        # print("[Success] download umdCd.xls")
    except Except as e:
        # print("[Error] fail to download umdCd.xls .", e)
        return None
    return data_path

def get_umdCd(data_path=None):
    if data_path is None:
        data_path = os.path.join(project_path(), 'src', 'data', 'umdCd.xls')
    umdcd = pd.read_excel(data_path, header=0)

    code = dict()
    umdcd['법정동코드'] = umdcd['법정동코드'].astype(str)
    # 지역코드
    code['11110'] = '서울특별시'
    # 법정동읍면동코드
    for _, row in umdcd.iterrows():
        code[row['법정동코드'][5:]] = row['법정동명'][6:]
    return code

def map_code_to_text():
    

    pass

# 도로명 주소 찾기.
def get_roadname(search_keywords, driver):
    # find location : https://www.ride.bz/
    pass

if __name__ == '__main__':
    import sys
    sys.path.append(
        os.path.dirname(os.path.dirname( # /mlops/
            os.path.dirname(  # /mlops/src
                os.path.abspath(__file__)  # /mlops/src/main.py
            )
        ))
    )

    from src.dataset.data_process import (
        read_dataset, apt_preprocess, train_val_split, 
        AptDataset, get_dataset
    )
    from src.dataset.data_loader import (
        S3PublicCSVDownloader
    )
    from src.utils.utils import init_seed
    from src.model.model_cards import model_save, LGBMRegressorCard, CatBoostRegressorCard
    from src.model.hyperparam_tuning import hyperparameter_tuning
    from src.evaluate.evaluate import cross_validation
    from src.inference.inference import load_checkpoint, load_model, get_inference_dataset, inference
    from src.utils.constant import Models

    # 데이터 로드
    # S3PublicCSVDownloader().download_csv(output_filename='../data/apt_trade_data.csv')

    # 데이터셋 및 DataLoader 생성
    apt = read_dataset('apt_trade_data.csv')
    print(apt.columns)
    # print(apt.shape)
    apt = apt_preprocess(apt)
    print(apt.head(3))

    get_data_umdCd()

