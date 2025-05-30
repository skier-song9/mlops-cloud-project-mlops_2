import os
import sys

sys.path.append(
    os.path.dirname( # /mlops/
        os.path.dirname(  # /mlops/src
            os.path.abspath(__file__)  # /mlops/src/main.py
        )
    )
)

from src.dataset.data_process import (
    read_dataset, apt_preprocess, train_val_split, 
    AptDataset, get_dataset
)
from src.utils.utils import init_seed
from src.model.model_cards import model_save, LGBMRegressorCard

init_seed()

if __name__ == '__main__':
    # 데이터셋 및 DataLoader 생성
    apt = read_dataset('apt_trade_data.csv')
    # print(apt.shape)
    apt = apt_preprocess(apt)
    # print(apt.shape)
    apt, folds_idx = train_val_split(
        df=apt,
        datetime_col='datetime',
        n_folds=3,
        val_months=3
    )
    # print(len(folds_idx))
    fold_datasets = get_dataset(df=apt, folds_index=folds_idx)
    full_dataset = AptDataset(
        df=apt, scaler="No", encoders=dict()
    )

    # train and evaluate with k_folds
    from tqdm import tqdm
    val_rmses = []
    for train_dataset, val_dataset in tqdm(fold_datasets):
        model = LGBMRegressorCard(
            train_dataset=train_dataset,
            val_dataset=val_dataset,
            early_stopping_rounds=50,
            random_seed=42
        )
        ### hyperparam tuning 여부
        # model.hyperparam_tuning()
        model.train()
        val_rmse = model.validate()
        val_rmses.append(val_rmse)
    import numpy as np
    val_rmse_result = np.mean(val_rmses)
    print(val_rmse_result,val_rmses)

    ### model_save
    model_save(
        model_card=model,
        val_loss=val_rmse_result,
        scaler=model.train_dataset.scaler,
        encoders=model.train_dataset.encoders
    )

    ### <<< run_train <<<
    ### >>> run_inference >>>

    ### model_load 


    # train only full_dataset
    model = LGBMRegressorCard(
        train_dataset=full_dataset,
        val_dataset=None,
        early_stopping_rounds=50,
        random_seed=42
    )
    model.train()

    ### inference

    

    



