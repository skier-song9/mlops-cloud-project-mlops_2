import os
import sys
import fire
from dotenv import load_dotenv


sys.path.append(
    os.path.dirname( # /mlops/
        os.path.dirname(  # /mlops/src
            os.path.abspath(__file__)  # /mlops/src/main.py
        )
    )
)

from src.dataset.data_process import (
    read_remote_dataset, apt_preprocess, train_val_split, 
    AptDataset, get_dataset
)
from src.dataset.getdatav2 import get_data_main
from src.utils.utils import init_seed, project_path
from src.model.model_cards import model_save, LGBMRegressorCard, CatBoostRegressorCard
from src.model.hyperparam_tuning import hyperparameter_tuning
from src.evaluate.evaluate import cross_validation
from src.inference.inference import load_checkpoint, load_model, get_inference_dataset, inference
from src.utils.constant import Models

init_seed()

def get_data(start=200701, end=None):
    get_data_main(start, end)
    
    
# >>> lee >>> getdata


# <<< lee <<<

# >>> song >>> run_geoprocess + run_prerprocess
from src.utils.utils import project_path, get_current_time
from src.dataset.data_geoprocess import get_unique_apt, get_location_dataframe, save_location_s3
import pandas as pd

def run_geoprocess():
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
# <<< song <<<

# >>> ahn >>> run_train, run_evaluate

# <<< ahn <<<

# >>> park >>> monitoring

# <<< park <<<

def run_train(model_name, tuning_max_evals=None):
    # tuning_max_evals 옵션을 설정하면 하이퍼파라미터 튜닝을 진행, 
    # 설정하지 않으면 하이퍼파라미터 튜닝 없이 validation 진행.
    Models.validation(model_name)

    # if wandb add codes.

    # 데이터셋 및 DataLoader 생성
    apt = read_remote_dataset('s3://mloops2/apt_trade_data.csv')
    # print(apt.shape)
    apt = apt_preprocess(apt)
    # print(apt.shape)
    apt, folds_idx = train_val_split(
        df=apt,
        datetime_col='datetime',
        n_folds=5,
        val_months=3
    )
    # print(len(folds_idx))
    fold_datasets = get_dataset(df=apt, folds_index=folds_idx)
    full_dataset = AptDataset(
        df=apt, scaler="No", encoders=dict()
    )

    # train and evaluate with folds
    model_card_class = Models[model_name.upper()].value
    model_card = model_card_class(
        early_stopping_rounds=50,
        random_seed=42
    )
    print("model_card_class=",model_card_class)
    print("model_card.model=", model_card.model)
    mean_val_score = float('inf')
    if tuning_max_evals is not None: # hyperparameter tuning
        model_card, mean_val_score = hyperparameter_tuning(
            model_card=model_card, fold_datasets=fold_datasets, max_evals=tuning_max_evals
        )
    else: # hyperparameter tuning 안 함
        model_card, mean_val_score = cross_validation(model_card, fold_datasets)

    # full dataset으로 전체 학습
    # 현재 시점 model_card는 best_param으로 초기화되었고, 학습은 안 된 상태임.
    model_card.train(train_dataset=full_dataset, val_dataset=None)    
    ### model_save
    model_save(
        model_card=model_card,
        val_loss=mean_val_score,
        scaler=full_dataset.scaler,
        encoders=full_dataset.encoders,
    )

def run_inference(model_name, dataset=None):
    Models.validation(model_name)
    model_card_class = Models[model_name.upper()].value

    checkpoint_path = load_checkpoint(model_card_class.name)
    model, scaler, val_loss, encoders, early_stopping_rounds, random_seed = load_model(checkpoint_path)

    ### inference
    # init model card
    model_card = model_card_class(early_stopping_rounds, random_seed)
    model_card.model = model
    # get client request dataset : 사용자가 검색한 아파트 주소를 바탕으로 inference용 데이터셋 생성
    test_dataset = get_inference_dataset(scaler, encoders)
    # inference : 모델 추론
    result = inference(model_card, test_dataset)
    # send result to web.
    

if __name__ == '__main__':

    load_dotenv(dotenv_path=f"{project_path()}/.env", override=True)

    fire.Fire({
        "get_data" : get_data,  
        'geoprocess':run_geoprocess,
        'preprocess':run_preprocess,
        "train": run_train,
        "inference": run_inference
    })