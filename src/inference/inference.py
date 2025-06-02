import os
import sys
import glob
import re
import joblib

sys.path.append(
    os.path.dirname(os.path.dirname( # /mlops/
        os.path.dirname(  # /mlops/src
            os.path.abspath(__file__)  # /mlops/src/main.py
        )
    ))
)

import numpy as np
import pandas as pd

from src.utils.utils import model_dir
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

def inference(model_card, test_dataset):
    result = model_card.inference(dataset=test_dataset)
    return result

if __name__=='__main__':
    from src.dataset.data_process import AptDataset, read_dataset, apt_preprocess, train_val_split
    apt = read_dataset('apt_trade_data.csv')
    apt = apt_preprocess(apt)
    apt, folds_idx = train_val_split(
        df=apt,
        datetime_col='datetime',
        n_folds=2,
        val_months=3
    )
    print(apt.columns)
    print(apt[['도로명주소','시군구법정동코드','단지명']].head())
    full_dataset = AptDataset(df=apt, scaler="No", encoders=dict())
    # 도로명주소 = 지역코드 + 법정동읍면동코드 + 도로명 + 지번