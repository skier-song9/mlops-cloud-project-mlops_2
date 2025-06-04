import os
import numpy as np
import pandas as pd
from dotenv import load_dotenv

from sklearn.preprocessing import LabelEncoder, StandardScaler
from category_encoders import TargetEncoder

import sys
sys.path.append(
    os.path.dirname(os.path.dirname( # /mlops/
        os.path.dirname(  # /mlops/src
            os.path.abspath(__file__)  # /mlops/src/dataset
        )
    ))
)
from src.utils.utils import project_path, get_current_time
from src.dataset.data_geoprocess import download_umdCd, get_umdCd

load_dotenv(dotenv_path=os.path.join(project_path(), '.env'))

def read_dataset(filepath):
    apt_filepath = os.path.join(project_path(), 'src','data',filepath)
    apt = pd.read_csv(apt_filepath)
    return apt

def read_remote_dataset(filepath):
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        print(e)
    return df

def process_area_binning(df):
    """ 전용면적을 구간화

    :param pd.DataFrame df: _description_
    :return pd.DataFame: _description_
    """
    labels=['소형','중형','대형','초대형']
    df['국평'] = pd.cut(
        df['전용면적'],
        bins=[0, 59, 84, 101, np.inf],
        labels=labels,
        right=True # 구간 범위: (A, B]
    )
    # print(f"add '국평' column.\nDomain={labels}")
    return df

def apt_preprocess(apt, only_column=False):
    column_names = {
        'aptDong':'아파트동명', 'aptNm':'단지명',
        'sggCd':'지역코드','umdNm':'법정동','jibun':'지번',
        'excluUseAr':'전용면적','dealYear':'계약년도','dealMonth':'계약월',
        'dealDay':'계약일','dealAmount':'target','floor':'층','buildYear':'건축년도',
        'cdealType':'해제사유','cdealDay':'해제사유발생일','dealingGbn':'거래유형',
        'estateAgentSggNm':'중개사소재지','rgstDate':'등기일자','slerGbn':'매도자',
        'buyerGbn':'매수자','landLeaseholdGbn':'토지임대부여부',
        'aptSeq':'단지일련번호','bonbun':'본번','bubun':'부번','roadNm':'도로명',
        'roadNmBonbun':'도로명건물본번','roadNmBubun':'도로명건물부번',
        'roadNmCd':'도로명코드', 'landCd':'법정동지번코드',
        'roadNmSeq':'도로명일련번호','roadNmSggCd':'도로명시군구코드',
        'roadNmbCd':'도로명지상지하코드','umdCd':'법정동읍면동코드'
    }
    apt = apt.rename(columns=column_names)

    # 사용할 컬럼만 추출
    extract_cols = [
        '단지명','지역코드','법정동읍면동코드','도로명','지번',
        '건축년도','매수자','계약일','계약월','계약년도',
        '거래유형','전용면적','층',
        '토지임대부여부','매도자',
        'target'
    ]
    apt = apt[extract_cols].copy()

    # translate code to text
    code_dict = None
    try: 
        code_dict = get_umdCd()
    except Exception as e: # if there is no file > download file first
        data_path = download_umdCd()
        code_dict = get_umdCd(data_path)
    if code_dict is None:
        raise ValueError("There is no UmdCode Information.")
    apt['지번'] = apt['지번'].astype(str)
    apt['지역코드'] = apt['지역코드'].astype(str)
    apt['법정동읍면동코드'] = apt['법정동읍면동코드'].astype(str)
    apt['시군구법정동코드'] = apt['지역코드'] + apt['법정동읍면동코드']  # 시+구+동 코드
    apt['시군구법정동코드'] = apt['시군구법정동코드'].apply(lambda x: code_dict[x]) # 시+구+동 문자열
    apt['시구'] = apt['시군구법정동코드'].apply(lambda x: " ".join(x.split(" ")[:-1])) # 시+구 문자열

    cols_todel = ['지역코드','법정동읍면동코드','도로명','지번']

    apt['지번주소'] = apt['시군구법정동코드'] + ' ' +apt['지번']
    apt['도로명주소'] = apt['시구'] + ' ' + apt['도로명']
    apt = apt.drop(columns=cols_todel, axis=1)

    if only_column:
        return apt

    ### get location X, Y
    location_data_url = os.getenv("S3_APT_LOCATION")
    location_data_url = location_data_url.replace(".csv", f"_{get_current_time(strformat='%y%m%d')}.csv")
    location_df = read_remote_dataset(location_data_url)
    apt = apt.merge(location_df[['지번주소','X','Y']], on='지번주소', how='left')

    ### drop 도로명주소
    apt = apt.drop(columns=['도로명주소'], axis=1)

    ### Deal with Missing Value
    apt['매수자'] = apt['매수자'].fillna('기타')
    apt['매도자'] = apt['매도자'].fillna('기타')
    apt['거래유형'] = apt['거래유형'].fillna('기타')
    apt['X'] = apt['X'].replace(0, np.nan)
    apt['Y'] = apt['Y'].replace(0, np.nan)
    longitude_median = apt['X'].median()
    latitude_median = apt['Y'].median()
    apt['X'] = apt['X'].fillna(longitude_median)
    apt['Y'] = apt['Y'].fillna(latitude_median)

    ### Date column
    apt['datetime'] = apt['계약년도'].astype(str)+'-'+apt['계약월'].astype(str)+'-'+apt['계약일'].astype(str)
    apt['datetime'] = pd.to_datetime(apt['datetime'])

    ### Outliers
    apt['층'] = apt['층'].apply(np.abs)

    ### modify dtype
    apt['target'] = apt['target'].str.replace(',','').astype(int)

    ### Derived features
    apt = process_area_binning(apt)

    apt['재건축가중치'] = apt['계약년도'] - apt['건축년도']

    return apt

def train_val_split(df:pd.DataFrame, datetime_col:str, n_folds:int=5, val_months:int=3):
    """ Timeseries Cross-Validation : 뒤쪽부터 3개월씩 window를 밀어가며 fold를 나눔

    ex) 데이터가 2025-05-20까지면
    fold 1
        - validation : 2025-05-20 ~ 02-20 (val_month 만큼)
        - train : 2025-02-20 ~ 끝까지
    fold 2
        - validation : 2025-02-20 ~ 2024-12-20 (val_month 만큼)
        - train : 2024-12-20 ~ 끝까지
    ...

    :param pd.DataFrame df: df to split
    :param str datetime_col: name of datetime column
    :param int n_folds: number of folds
    :param val_months df: month of validation data
    :return : sorted_df, folds_idx
    """
    assert datetime_col in df.columns
    # 정렬
    df = df.sort_values(datetime_col)
    max_date = df[datetime_col].max()
    folds_idx = []
    for i in range(n_folds):
        # validation 기간
        val_end = max_date - pd.DateOffset(months=val_months * i)
        val_start = max_date - pd.DateOffset(months=val_months * (i+1))

        # 인덱스 추출
        val_idx = df[(df[datetime_col] >= val_start) & (df[datetime_col] < val_end)].index.tolist()
        train_idx = df[df[datetime_col] < val_start].index.tolist()

        folds_idx.append((train_idx, val_idx))
    if 'datetime' in df.columns:
        df = df.drop(columns=['datetime'], axis=1)
    return df, folds_idx  

class AptDataset:
    def __init__(self, df, scaler=None, encoders=dict()):
        self.df = df
        self.label_encoding_columns = ['매수자','거래유형','토지임대부여부','매도자','국평']
        self.target_encoding_columns = ['지번주소','시구','단지명']

        # ✅ 존재 여부 검증
        missing_cols = [col for col in self.label_encoding_columns if col not in df.columns]
        assert not missing_cols, f"❌ 다음 컬럼이 df에 없습니다: {missing_cols}"
        missing_cols = [col for col in self.target_encoding_columns if col not in df.columns]
        assert not missing_cols, f"❌ 다음 컬럼이 df에 없습니다: {missing_cols}"
        del missing_cols

        self.scaler = scaler
        self.encoders = encoders

        self._encoding()
        self.features = self.df.drop(columns=['target'], axis=1).values
        self.target = self.df['target'].values
        if scaler != "No":
            self._scaling()

    def _encoding(self):
        # Label Encoding
        for lec in self.label_encoding_columns:
            e = self.encoders.get(lec, False)
            if e: # 기존 encoder가 존재하면 transform만 적용
                self.df[lec] = e.transform(self.df[lec])
            else: # 기존 encoder가 없으면 fit_transform하고 encoders 딕셔너리에 저장.
                e = LabelEncoder()
                self.df[lec] = e.fit_transform(self.df[lec])
                self.encoders[lec] = e
        # Target encoding
        e = self.encoders.get('target', False)
        if e:
            self.df[self.target_encoding_columns] = e.transform(self.df[self.target_encoding_columns])
        else:
            e = TargetEncoder(cols=self.target_encoding_columns, smoothing=10.0)
            self.df[self.target_encoding_columns] = e.fit_transform(self.df[self.target_encoding_columns], self.df['target'])
            self.encoders['target'] = e

    def _scaling(self):
        if self.scaler:
            self.features = self.scaler.transform(self.features)
        else:
            self.scaler = StandardScaler()
            self.features = self.scaler.fit_transform(self.features)

    @property
    def features_dim(self):
        return self.features.shape[1]
    def __len__(self):
        return len(self.target)
    def __getitem__(self, idx):
        return self.features[idx], self.target[idx]
    
def get_dataset(df, folds_index):
    fold_datasets = []
    for train_idx, val_idx in folds_index:
        train = df.iloc[train_idx].copy()
        val = df.iloc[val_idx].copy()
        train_dataset = AptDataset(train, scaler="No", encoders=dict())
        val_dataset = AptDataset(val, scaler="No", encoders=train_dataset.encoders)
        fold_datasets.append((train_dataset, val_dataset))
    return fold_datasets

def run_geoprocess():
    from dotenv import load_dotenv
    import pandas as pd
    import os

    load_dotenv(dotenv_path=os.path.join(project_path(), '.env'))
    remote_raw_datapath = os.getenv("S3_URL")
    # 데이터 파이프라인 주기에 맞춰 다운로드 URL 수정
    remote_raw_datapath = remote_raw_datapath.replace(".csv", f"_{get_current_time(strformat='%y%m%d')}.csv")
    # download apt raw data
    apt = pd.read_csv(remote_raw_datapath)
    # process columns
    apt = apt_preprocess(apt, only_column=True)
    apt_unique = get_unique_apt(apt)
    for _ in range(5):
        # web crawling을 통해 좌표 검색
        apt_unique = get_location_dataframe(apt_unique, num_workers=8)
        if apt_unique[apt_unique['X']==0].shape[0] < 1:
            break
    # 좌표 데이터프레임을 S3에 업로드
    apt_unique = save_location_s3(apt_unique)

def run_preprocess():
    from dotenv import load_dotenv
    import pandas as pd
    import os

    load_dotenv(dotenv_path=os.path.join(project_path(), '.env'))
    remote_raw_url = os.getenv("S3_URL")
    # 데이터 파이프라인 주기에 맞춰 다운로드 URL 수정
    remote_raw_url = remote_raw_url.replace(".csv", f"_{get_current_time(strformat='%y%m%d')}.csv")
    # read data from S3
    apt = read_remote_dataset(remote_raw_url)
    # preprocess 
    apt = apt_preprocess(apt)
    # upload processed apt dataframe to S3
    upload_url = os.getenv("S3_APT_PROCESSED")
    upload_url = upload_url.replace(".csv", f"_{get_current_time(strformat='%y%m%d')}.csv")
    print(apt.columns)
    print(apt.isnull().sum())
    apt.to_csv(upload_url, index=False)

if __name__ == '__main__':
    import sys
    sys.path.append(
        os.path.dirname(os.path.dirname( # /mlops/
            os.path.dirname(  # /mlops/src
                os.path.abspath(__file__)  # /mlops/src/main.py
            )
        ))
    )

    from src.dataset.data_geoprocess import (
        save_location_s3, get_location_dataframe, get_unique_apt
    )
    # run_geoprocess()
    # run_preprocess()