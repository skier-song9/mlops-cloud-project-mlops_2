import os
import shutil
import glob
import zipfile
import time
import pandas as pd
from dotenv import load_dotenv
import re
import requests
from tqdm import tqdm
from multiprocessing import Pool, cpu_count
import subprocess

from selenium import webdriver 
from selenium.webdriver.common.by import By # 위치 지정자(css셀렉터,xpath,id 등)를 위한 클래스
from selenium.webdriver.common.keys import Keys # 키보드 키값이 정의된 클래스
from selenium.common.exceptions import TimeoutException,NoSuchElementException # 요소를 못 찾을 경우 예외처리용
from selenium.webdriver.support import expected_conditions as EC # Explicit Wait 사용 시
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoAlertPresentException
from geopy.geocoders import Nominatim
import tempfile

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
    unique_user_data_dir = tempfile.mkdtemp() # 임시 폴더를 생성
    options.add_argument(f"--user-data-dir={unique_user_data_dir}") # chrome driver의 data 폴더가 충돌하지 않게 임시 폴더를 사용
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    options.add_argument('--headless=new') # 창을 띄우지 않고 실행
    driver = webdriver.Chrome(
        options=options
    )
    # resize the window size
    driver.set_window_size(width=1280 , height=960)
    return driver, unique_user_data_dir

def clean_chrome_temp(temp_dir):
    try:
        subprocess.run(f"rm -rf {temp_dir}", shell=True)
    except:
        pass
    # chrome_temp_patterns = [
    #     '/tmp/.com.google.Chrome*',
    #     '/tmp/.org.chromium.Chromium*'
    # ]
    # for pattern in chrome_temp_patterns:
    #     try:
    #         subprocess.run(f"rm -rf {pattern}", shell=True)
    #     except:
    #         pass
        # for path in glob.glob(pattern):
        #     try:
        #         if os.path.isdir(path):
        #             shutil.rmtree(path, ignore_errors=True)
        #         elif os.path.isfile(path):
        #             os.remove(path)
        #     except Exception as e:
        #         print(f"⚠️ Failed to remove {path}: {e}")

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
    except Exception as e:
        # print("[Error] fail to download umdCd.xls .", e)
        return None
    return data_path

def get_umdCd(data_path=None):
    if data_path is None:
        data_path = os.getenv("S3_URL_UMDCD")
    
    umdcd = pd.read_excel(data_path, header=0)

    code = dict()
    umdcd['법정동코드'] = umdcd['법정동코드'].astype(str)
    # 법정동읍면동코드
    for _, row in umdcd.iterrows():
        code[row['법정동코드']] = row['법정동명']
    return code

def correct_lat_lon(X, Y):
    """
    위도(lat)와 경도(lon)를 입력받아, 한국 범위를 기준으로
    위경도가 뒤바뀌었는지 판단하고, 올바른 순서로 반환합니다.
    """
    lat = Y
    lon = X
    # 위도와 경도 범위 (한국 기준)
    is_lat_valid = 32 <= lat <= 45
    is_lon_valid = 123 <= lon <= 133

    if is_lat_valid and is_lon_valid:
        # 둘 다 정상 범위 → 순서가 맞음
        return lon, lat
    elif 32 <= lon <= 45 and 123 <= lat <= 133:
        # 서로 뒤바뀜 → 순서 바꿔서 반환
        return lat, lon
    else:
        # 둘 다 범위 벗어남 → 오류 가능성
        raise ValueError(f"잘못된 위도/경도 입력: lat={lat}, lon={lon}")

def get_roadname(jibun, driver):
    # 도로명 찾기
    try:
        driver.get("https://www.juso.go.kr/openIndexPage.do")
        search_input = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'mainSearchBoxBasic__searchAdressTyping'))
        )
        search_input.send_keys(jibun)
        search_input.send_keys(Keys.ENTER)
        # total_result_number = WebDriverWait(driver, 3).until(
        #     EC.presence_of_element_located((By.CSS_SELECTOR, '#totalResultBox > div.resultLayerPopup__innerWrap > p > strong:nth-child(2)'))
        # ).text
        first_result = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.resultLayerPopup__list li:first-of-type .resultLayerPopup__detailBox .resultLayerPopup__listDetail .resultLayerPopup__listDetailContent.pcContent .resultLayerPopup__innerBox .roadNameText'))
        ).text
        ### 괄호를 제거
        first_result = re.sub(r"\s*\(.*?\)", "", first_result)
        first_result = first_result.strip()
        # update 도로명
        roadname = first_result
        # print(f"🔸Updated to Roadname : {roadname}")
        return roadname
    except Exception as e:
        # print("[Error] finding roadname.")
        return None

# 도로명 주소로 좌표 찾기.
def get_location(search_keyword, driver):
    """ 
    1. get roadname

    :param tuple(str,str) search_keywords: (지번주소, 도로명주소)
    :param selenium.WebDriver driver: Chrome driver from get_driver()
    :return tuple: (X,Y). X is latitude(경도), Y is longitude(위도).
    """
    # first url : https://www.ride.bz/%ec%a7%80%eb%8f%84/
    # second url : https://www.findlatlng.org/
    driver.get("https://www.ride.bz/%ec%a7%80%eb%8f%84/")
    # 검색창 찾기
    search_input = WebDriverWait(driver, 3).until(
        EC.presence_of_element_located((By.ID, 'address'))
    )
    # 검색어 입력
    search_input.send_keys(search_keyword)
    # 검색어 검색
    search_submit = WebDriverWait(driver, 3).until(
        EC.presence_of_element_located((By.ID, 'submit'))
    )
    search_submit.click()
    # 위도 경도 텍스트 찾기
    try:
        time.sleep(2)
        # 알람창이 있으면 검색결과가 없는 것
        alert = driver.switch_to.alert
        alert.accept()
    except NoAlertPresentException as e:
        X = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.ID, 'longitude')) # 경도
        ).text
        Y = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.ID, 'latitude')) # 위도
        ).text
        X, Y = float(X), float(Y)
        # 위도 경도 검색결과 있는 경우 > return (경도, 위도)
        X, Y = correct_lat_lon(X, Y)
        # print(f"✅ searched in ride.bz : {search_keyword}, {X} , {Y} ")
        return (X,Y)    
    try:
        # 위도 경도 검색결과 없는 경우 > second_url로 다시 검색
        driver.get("https://www.findlatlng.org/")
        search_input = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                '#__nuxt > div > div.row.mt-1 > div > div.form-group > div > input'))
        )
        search_input.send_keys(search_keyword)
        search_input.send_keys(Keys.ENTER)
        time.sleep(2)
        searched_address = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 
                '#__nuxt > div > div.container-fluid.pb-3.fw-bold'))
        ).text
        # find lat long
        searched_address = searched_address.split('\n')[-1] # 위도(Latitude) : 37.5436917758825 / 경도(Longitude) : 127.018895964412
        searched_split = searched_address.split(' ')
        split_length = len(searched_split)
        X, Y = [float(searched_split[6]), float(searched_split[2])]
        X, Y = correct_lat_lon(X, Y)
        # print(f"✅ searched in findlatlng : {search_keyword}, {X} , {Y} ")
        return (X,Y)
    except (TimeoutException,NoSuchElementException, IndexError) as e:
        try:
            # 최후 : geopy 활용
            geolocator = Nominatim(user_agent='South_Korea')
            location = geolocator.geocode(search_keyword)
            if location is not None: # 좌표를 찾지 못함
                X = location.point.longitude
                Y = location.point.latitude
                X, Y = correct_lat_lon(X, Y)
                # print(f"✅ searched in geopy : {search_keyword}, {X} , {Y} ")
                return (X,Y)
        except Exception as e:
            print(e)
            pass
    # print("Fail all process")
    return (0, 0) # 검색결과 없는 경우

def get_unique_apt(apt:pd.DataFrame):
    apt_unique = apt[['지번주소', '도로명주소']].copy()
    apt_unique = apt_unique.drop_duplicates()
    print(apt_unique.shape[0])
    apt_unique['X'] = 0.0
    apt_unique['Y'] = 0.0
    return apt_unique

def process_address(args):
    """_summary_

    :param _type_ args: _description_
    :return _type_: _description_
    """
    idx, row = args
    jibun = row['지번주소']
    roadname = row['도로명주소']
    driver = None
    temp_dir = None
    try:
        driver, temp_dir = get_driver()
        X,Y = get_location(jibun, driver)
        if X != 0:
            return idx, X, Y, temp_dir
        new_roadname = get_roadname(jibun, driver)
        if new_roadname:
            X,Y = get_location(new_roadname, driver)
        else:
            X,Y = get_location(roadname, driver)
        return idx, X, Y, temp_dir
    except Exception as e:
        print(f"Error at index {idx}: {e}\nSearch Jibun:{row['지번주소']}")
        return idx, 0, 0, temp_dir
    finally:
        if driver:
            driver.quit()
            # clean_chrome_temp(temp_dir)

def get_location_dataframe(apt_unique, num_workers=1):
    """ unique한 지번주소/도로명주소의 X,Y 좌표를 구하는 함수.
    num_workers를 설정하면 multi-process 로 진행

    :param pd.DataFrame apt_unique: 
    :param int num_workers: defaults to None
    :return pd.DataFrame: location_df
    """
    if num_workers > 1:
        num_workers = max(num_workers, cpu_count()-1)

    # x,y 좌표가 0인 주소만 좌표 찾기
    location_df = apt_unique.copy()
    apt_unique = apt_unique.reset_index(drop=False)
    apt_unique = apt_unique[apt_unique['X']==0.0]
    apt_unique = apt_unique.set_index('index')
    print("Number of data to update:", apt_unique.shape[0])

    # 멀티프로세싱
    results = []
    temp_dirs = []
    with Pool(processes=num_workers) as pool:
        # results = list(tqdm(pool.imap(process_address, apt_unique.iterrows()), total=len(apt_unique)))
        # 일정 주기마다 clean_chrome_temp()로 크롬 드라이버 임시 저장 공간을 정리.
        for i, result in enumerate(tqdm(pool.imap_unordered(process_address, apt_unique.iterrows()), total=len(apt_unique))):
            idx, x, y, temp_dir = result
            results.append((idx, x, y))
            if temp_dir:
                temp_dirs.append(temp_dir)
            if (i + 1) % 100 == 0:
                # print(f"🧹 Cleaning Chrome temp files at {i + 1} items...")
                for td in temp_dirs:
                    clean_chrome_temp(td)
                temp_dirs = []

    # 결과 반영
    for idx, x, y in results:
        location_df.loc[idx, 'X'] = x
        location_df.loc[idx, 'Y'] = y

    return location_df


def save_location_s3(df):
    try:
        load_dotenv(dotenv_path=os.path.join(project_path(), '.env'))
        url = os.getenv('S3_APT_LOCATION')
        url = url.replace(".csv", f"_{get_current_time(strformat='%y%m%d')}.csv")
        print("URL:", url)
        df.to_csv(url, index=False)
        print("Saved")
    except Exception as e:
        print(e)
        pass
    return df

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
        AptDataset, get_dataset, read_remote_dataset
    )
    from src.dataset.data_loader import (
        S3PublicCSVDownloader
    )
    from src.utils.utils import init_seed, project_path
    from src.model.model_cards import model_save, LGBMRegressorCard, CatBoostRegressorCard
    from src.model.hyperparam_tuning import hyperparameter_tuning
    from src.evaluate.evaluate import cross_validation
    from src.inference.inference import load_checkpoint, load_model, get_inference_dataset, inference
    from src.utils.constant import Models

    # 데이터 로드
    # S3PublicCSVDownloader().download_csv(output_filename='../data/apt_trade_data.csv')

    # 데이터셋 및 DataLoader 생성
    # apt = read_dataset('apt_trade_data.csv')
    # print(apt.columns)
    # print(apt.shape)
    # apt = apt_preprocess(apt)
    # apt = apt_preprocess(apt, only_column=True)
    # apt_unique = get_unique_apt(apt)
    # apt_unique = read_remote_dataset("s3://mloops2/apt_location_250604.csv")
    # apt_location = get_location_save_s3(apt_unique, num_workers=6)
    # print(apt_location[apt_location['X']!=0].shape[0])
    # apt_location.to_csv(os.path.join(project_path(), 'src','data','apt_location.csv'), index=False)
    # apt_location.to_csv(os.path.join(project_path(), 'src','data','apt_location.csv'), index=False)
    # print(apt.head(3))
    # driver = None
    # try:
    #     for idx, row in apt.iterrows():
    #         search_keywords = (row['지번주소'], row['도로명주소'])
    #         # print(search_keywords)
    #         driver = get_driver()
    #         X,Y = get_location(search_keywords, driver)
    #         driver.quit()
    #         clean_chrome_temp()
    #         if idx == 3: break
    # finally:
    #     if driver:
    #         time.sleep(5)
    #         driver.quit()
    #         clean_chrome_temp()