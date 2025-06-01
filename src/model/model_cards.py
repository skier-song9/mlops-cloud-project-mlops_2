import os
import joblib
from abc import ABC, abstractmethod

import numpy as np
import lightgbm as lgb
from lightgbm import LGBMRegressor
from catboost import CatBoostRegressor

from src.utils.utils import model_dir, get_current_time

def model_save(model_card, val_loss, scaler, encoders):
    save_dir = model_dir(model_card.name)
    os.makedirs(save_dir, exist_ok=True)

    current_time = get_current_time()
    dst_path = os.path.join(
        save_dir, f"VL{int(val_loss)}_T{current_time}.pkl"
    )

    save_data = {
        "model": model_card.model,
        "val_loss": val_loss,
        "scaler": scaler,
        "encoders": encoders,
        "early_stopping_rounds": model_card.early_stopping_rounds,
        "random_seed": model_card.random_seed
    }
    with open(dst_path, 'wb') as f:
        joblib.dump(save_data, f)


class ModelCard(ABC):
    def __init__(self):
        pass
    @abstractmethod
    def init_model(self, params):
        pass
    @abstractmethod
    def train(self, train_dataset, val_dataset=None):
        pass
    @abstractmethod
    def inference(self, dataset):
        pass


class LGBMRegressorCard(ModelCard):
    name = "LGBMRegressor"

    def __init__(self, early_stopping_rounds=50, random_seed=42):
        super().__init__()
        self.early_stopping_rounds = early_stopping_rounds
        self.random_seed = random_seed

        self.params = { # basic params
            'n_estimators':3000,
            'objective':'regression',
            'boosting_type':'gbdt',
        }
        self.model = self.init_model(self.params)

    def init_model(self, params):
        self.model = LGBMRegressor(
            **params,
            metric='rmse',
            random_state=self.random_seed,
            n_jobs=8, # use 8 cpu processor
        )
    
    def train(self, train_dataset, val_dataset=None):
        if val_dataset is None:
            self.model.fit(
                train_dataset.features, train_dataset.target,
                eval_metric='rmse'
            )
        else:
            self.model.fit(
                train_dataset.features, train_dataset.target,
                eval_set=[(train_dataset.features, train_dataset.target), (val_dataset.features, val_dataset.target)],
                eval_metric='rmse',
                callbacks=[
                    lgb.early_stopping(stopping_rounds=self.early_stopping_rounds)
                ]
            )

    def inference(self, dataset):
        preds = self.model.predict(dataset.features)
        return preds

class CatBoostRegressorCard(ModelCard):
    name = 'CatBoostRegressor'

    def __init__(self, early_stopping_rounds=50, random_seed=42):
        super().__init__()
        self.early_stopping_rounds = early_stopping_rounds
        self.random_seed = random_seed

        self.params = { # basic params
            'n_estimators':3000,
            'objective':'regression',
            'boosting_type':'gbdt',
        }
        self.model = self.init_model(self.params)

    def init_model(self, params):
        self.model = CatBoostRegressor(
            **params,
            random_state=self.random_seed,
            early_stopping_rounds=self.early_stopping_rounds,
            verbose=0,
            loss_function='RMSE',
            eval_metric='RMSE'
        )
    
    def train(self, train_dataset, val_dataset=None):
        if val_dataset is None:
            self.model.fit(
                train_dataset.features, train_dataset.target
            )
        else:
            self.model.fit(
                train_dataset.features, train_dataset.target,
                eval_set=[(train_dataset.features, train_dataset.target), (val_dataset.features, val_dataset.target)],
            )

    def inference(self, dataset):
        preds = self.model.predict(dataset.features)
        return preds
    
if __name__ == '__main__':
    pass
    # print(CatBoostRegressorCard.name) # > CatBoostRegressor
    # print(CatBoostRegressorCard.__name__) # > CatBoostRegressorCard