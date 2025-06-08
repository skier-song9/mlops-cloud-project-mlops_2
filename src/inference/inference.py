import os
import sys
import glob
import re
import joblib
import datetime

sys.path.append(
    os.path.dirname(os.path.dirname( # /mlops/
        os.path.dirname(  # /mlops/src
            os.path.abspath(__file__)  # /mlops/src/main.py
        )
    ))
)

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.font_manager as fm
import matplotlib.dates as mdates

from src.utils.utils import model_dir, project_path, get_current_time
from src.dataset.data_process import AptDataset, read_dataset, apt_preprocess, train_val_split
from src.model.model_cards import LGBMRegressorCard, CatBoostRegressorCard

def load_checkpoint(model_name):
    assert model_name in ['LGBMRegressor', 'CatBoostRegressor']
    target_dir = model_dir(model_name)
    models_path = os.path.join(target_dir,"*.pkl")
    every_models_path = glob.glob(models_path)

    # 정규표현식 패턴: VL{}_T{}.pkl
    pattern = re.compile(r'VL(\d+)_T(\d+)\.pkl')
    model_infos = []
    for path in every_models_path:
        filename = os.path.basename(path)
        match = pattern.match(filename)
        if match:
            val_loss = int(match.group(1))
            ct = match.group(2)
            model_infos.append((val_loss,ct,path))
    if not model_infos:
        raise ValueError("Saved model doesn't exist.")
    model_infos.sort(key=lambda x: (x[0], -int(x[1])))
    best_n_recent_model_path = model_infos[0][2]
    return best_n_recent_model_path

def load_model(checkpoint_path):
    with open(checkpoint_path, 'rb') as f:
        bundle = joblib.load(f)

        model = bundle['model']
        scaler = bundle['scaler']
        val_loss = bundle['val_loss']
        encoders = bundle['encoders']
        early_stopping_rounds = bundle["early_stopping_rounds"]
        random_seed = bundle["random_seed"]
    return model, scaler, val_loss, encoders, early_stopping_rounds, random_seed

def get_inference_dataset(scaler, encoders):
    """
    ex)
             = 지역코드 + 법정동읍면동코드 + 도로명 + 지번
    도로명주소 = 11260 10100 중랑천로 193-1
                    = 지역코드 + 법정동읍면동코드
    시군구법정동코드 = 1126010100

    단지명 = 면목한신
    """
    roadname = '11260 10100 중랑천로 193-1' # 사용자가 검색한 아파트 주소라고 하자.

    apt = read_dataset('apt_trade_data.csv')
    # 1. 해당 도로명주소와 일치하는 데이터가 있는지 탐색


    return None

def get_inference_dataframe(apt_process, lat, lng):
    """
    process
    1. apt_process에서 [단지명, 건축년도, 매수자, 거래유형, 전용면적, 층, 토지임대여부, 매도자, 시군구법정동코드, 시구, 지번주소, X, Y, 국평, 재건축가중치] 컬럼만 추출하여 apt_process로 저장한다.
    2. drop_duplicates
    3. apt_process의 X(longitude), Y(latitude) 컬럼을 사용하여 좌표를 기준으로 반경 50m의 geometry 컬럼을 추가해라. > geoDataFrame으로 변환
    4. apt_process에 'isContain' 컬럼으로 함수에 전달된 lat,lng이 데이터의 50m 반경에 포함되지 여부를 추가한다.
    5. apt_process에 'distance' 컬럼으로 함수에 전달된 lat,lng과 데이터의 Y,X와의 맨허튼 거리를 측정하여 추가한다.
    6. distance 컬럼을 오름차순 정렬한다. 
    7. 첫번째 row의 isContain이 1이면, 첫번째 row를 selected_rows에 추가한다.
        a) get_current_time으로 오늘날짜를 불러오고 오늘날짜로부터 90일 후까지 date_range를 만든다.
        b) selected_rows로 행이 90개인 데이터프레임을 만들고 datetime 컬럼으로 date_range를 추가한다.
        c) datetime 컬럼으로부터 계약일, 계약월, 계약년도 컬럼을 만든다. 
        d) 계약년도 - 건축년도 를 통해 '재건축가중치' 컬럼을 업데이트 한다.
        > selected_df
    8. 만약 7번에서 첫번째 row의 isContain이 0이면 첫번째~5번째 row들을 selected_rows에 추가한다.
        각각의 selected_rows에 대해 7번의 a,b,c,d를 반복한다. >> 총 450개 행 생성.
        > selected_df
    9. selected_df 를 반환한다.

    :param pd.DataFrame apt_process: dataframe for search
    :param float lat: latitude for search
    :param float lng: longitude for search
    :return pd.DataFrame selected_df: inference dataframe
    """
    # 1. 필요한 컬럼만 추출
    columns_to_keep = ['단지명', '건축년도', '매수자', '거래유형', '전용면적', '층', 
                       '토지임대부여부', '매도자', '시군구법정동코드', '시구', '지번주소', 
                       'X', 'Y', '국평', '재건축가중치']
    apt_process = apt_process[columns_to_keep].copy()
    # 2. 중복 제거
    apt_process = apt_process.drop_duplicates()
    # 3. 반경 50m geometry 컬럼 추가
    apt_process['geometry'] = [Point(xy) for xy in zip(apt_process['X'], apt_process['Y'])]
    apt_process = gpd.GeoDataFrame(apt_process, geometry='geometry', crs='EPSG:4326')
    apt_process = apt_process.to_crs(epsg=5179)  # 대한민국 기준 좌표계로 변환 (미터 단위)
    apt_process['buffer'] = apt_process.buffer(50)
    # 4. lat, lng 포함 여부
    point = gpd.GeoSeries([Point(lng, lat)], crs='EPSG:4326').to_crs(epsg=5179).iloc[0]
    apt_process['isContain'] = apt_process['buffer'].apply(lambda g: g.contains(point)).astype(int)
    # 5. 맨해튼 거리 추가 (미터 단위)
    target_point = apt_process.crs  # 5179 CRS
    apt_process['distance'] = apt_process.geometry.apply(lambda p: abs(p.x - point.x) + abs(p.y - point.y))
    # 6. 거리 기준 정렬
    apt_process = apt_process.sort_values(by='distance').reset_index(drop=True)
    selected_rows = []
    today = pd.to_datetime(get_current_time('%Y-%m-%d'))
    if apt_process.loc[0, 'isContain'] == 1:
        row = apt_process.iloc[[0]].copy()
        date_range = pd.date_range(today, today + pd.Timedelta(days=89))
        row = pd.concat([row] * len(date_range), ignore_index=True)
        row['datetime'] = date_range
        row['계약일'] = row['datetime'].dt.day
        row['계약월'] = row['datetime'].dt.month
        row['계약년도'] = row['datetime'].dt.year
        row['재건축가중치'] = row['계약년도'] - row['건축년도']
        selected_df = row
    else:
        for i in range(min(5, len(apt_process))):
            row = apt_process.iloc[[i]].copy()
            date_range = pd.date_range(today, today + pd.Timedelta(days=89))
            row = pd.concat([row] * len(date_range), ignore_index=True)
            row['datetime'] = date_range
            row['계약일'] = row['datetime'].dt.day
            row['계약월'] = row['datetime'].dt.month
            row['계약년도'] = row['datetime'].dt.year
            row['재건축가중치'] = row['계약년도'] - row['건축년도']
            selected_rows.append(row)
        selected_df = pd.concat(selected_rows, ignore_index=True)

    select_columns = columns_to_keep + ['계약일','계약월','계약년도','datetime']
    selected_df = selected_df[select_columns]
    return selected_df

def plot_prediction(pred_df, savepath):
    """
    1) figure의 figsize는 width=950px, height=450px에 맞춰 설정
    2) datetime 컬럼을 x축으로, target컬럼을 y축으로하고,
    3) X 라벨은 "시간", Y라벨은 "실거래가"로 설정
    4) seaborn.lineplot으로 그래프를 만들기. 
        errorbar는 조금 나오게 설정, X ticks 값들은 한 달 주기로 표시되도록 설정. x ticks rotation = 45 , x ticks 날짜형식은 YY-MM-DD 로.

    :param pd.DataFrame pred_df: _description_
    :param str savepath: path for plt.savefig
    :return str: plt save path
    """
    fe = fm.FontEntry(
        fname='/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf', # ttf 파일 저장 경로
        name='NanumBarunGothic' # 별칭
    )
    fm.fontManager.ttflist.insert(0,fe)
    plt.rcParams.update({'font.family' : 'NanumBarunGothic'}) # 한글 패치
    plt.rc('font', family='NanumBarunGothic')
    plt.rcParams['axes.unicode_minus'] =False # 음수 부호 안 깨지게

    # 1. 픽셀을 인치로 변환
    plt.figure(figsize=(10, 5), dpi=100)
    # 2. 라인플롯 그리기
    # 문자열이라면 datetime으로 변환
    pred_df["datetime"] = pd.to_datetime(pred_df["datetime"], errors="coerce")
    sns.lineplot(data=pred_df, x='datetime', y='target', errorbar='ci', linewidth=2)
    # 3. 라벨 설정
    plt.xlabel("년/월/일")
    plt.ylabel("실거래가 (단위: 만 원)", rotation=90)
    # 4. x축 설정 - 월 단위, 회전, 포맷
    plt.xticks(rotation=45)
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%y/%m/%d'))
    plt.tight_layout()
    plt.grid(True)
    # 5. 저장
    plt.savefig(savepath)
    plt.clf()
    return savepath

def inference(model_card, test_dataset):
    result = model_card.inference(dataset=test_dataset)
    return result

if __name__=='__main__':
    # from src.dataset.data_process import AptDataset, read_dataset, apt_preprocess, train_val_split
    # apt = read_dataset('apt_trade_data.csv')
    # apt = apt_preprocess(apt)
    # apt, folds_idx = train_val_split(
    #     df=apt,
    #     datetime_col='datetime',
    #     n_folds=2,
    #     val_months=3
    # )
    # print(apt.columns)
    # print(apt[['도로명주소','시군구법정동코드','단지명']].head())
    # full_dataset = AptDataset(df=apt, scaler="No", encoders=dict())
    # 도로명주소 = 지역코드 + 법정동읍면동코드 + 도로명 + 지번
    
    
    sys.path.append(
        os.path.dirname(
            os.path.dirname( # /mlops/
                os.path.dirname(  # /mlops/src
                    os.path.abspath(__file__)  # /mlops/src/main.py
                )
            )
        )
    )
    from src.utils.utils import project_path, get_current_time
    from src.dataset.data_process import AptDataset, read_remote_dataset, apt_preprocess

    # load processed dataset from S3
    print("✅ start S3_APT_PROCESSED download")
    current_datetime = get_current_time(strformat="%y%m%d", timedeltas=1)
    s3_url = os.getenv("S3_APT_PROCESSED").replace(".csv",f"_{current_datetime}.csv")
    # apt = read_remote_dataset(filepath=s3_url)
    # apt.to_csv(os.path.join(project_path(), 'src','data','apt_preprocess.csv'), index=False)
    apt = pd.read_csv(os.path.join(project_path(), 'src','data','apt_preprocess.csv'))
    print("✅ S3_APT_PROCESSED download finished")
    # get scaler, encoder
    full_dataset = AptDataset(
        df=apt, scaler="No", encoders=dict()
    )
    scaler, encoders = full_dataset.scaler, full_dataset.encoders

    # get_inference_dataframe
    # selected_df = get_inference_dataframe(apt, 37.310785, 126.278174)
    # selected_df.to_csv(os.path.join(project_path(), 'src','data','selected_df_far.csv'),index=False)
    selected_df = pd.read_csv(os.path.join(project_path(), 'src','data','selected_df_far.csv'))
    print("saved")

    import random
    random_numbers = random.sample(range(5000, 10001), 450)
    selected_df['target'] = random_numbers
    current_time = get_current_time(strformat="%y%m%d")
    savedir = os.path.join(project_path(), 'src', 'assets', 'plots', current_time)
    os.makedirs(savedir, exist_ok=True)
    savepath = os.path.join(savedir, f'{roadname.replace(" ", "_")}.png')
    savepath = plot_prediction(selected_df,'roadname_1')


