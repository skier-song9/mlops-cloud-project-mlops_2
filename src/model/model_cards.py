import os
import joblib
import datetime
from zoneinfo import ZoneInfo

import numpy as np
import lightgbm as lgb
from lightgbm import LGBMRegressor
from hyperopt import hp,STATUS_OK, fmin, tpe, Trials
from hyperopt.pyll.base import scope
from sklearn.model_selection import KFold
from sklearn.metrics import root_mean_squared_error

from src.utils.utils import model_dir

def model_save(model_card, val_loss, scaler, encoders):
    save_dir = model_dir(model_card.name)
    os.makedirs(save_dir, exist_ok=True)

    kst = ZoneInfo("Asia/Seoul")
    current_time = datetime.datetime.now(kst).strftime('%y%m%d%H%M%S')
    dst_path = os.path.join(
        save_dir, f"VL{int(val_loss)}_T{current_time}.pkl"
    )

    save_data = {
        "model": model_card.model,
        "val_loss": val_loss,
        "scaler": None if scaler == "No" else scaler,
        "encoders": encoders
    }
    with open(dst_path, 'wb') as f:
        joblib.dump(save_data, f)

class LGBMRegressorCard:
    name = "LGBMRegressor"

    def __init__(self, train_dataset, val_dataset=None, early_stopping_rounds=50, random_seed=42):
        self.train_dataset = train_dataset
        self.val_dataset = val_dataset
        self.early_stopping_rounds = early_stopping_rounds
        self.random_seed = random_seed

        self.search_space = {
            'num_leaves': scope.int(hp.quniform('num_leaves', 20, 150, 1)),
            'max_depth': scope.int(hp.quniform('max_depth', 3, 15, 1)),
            'learning_rate': hp.qloguniform('learning_rate', np.log(0.01), np.log(0.2), 0.01),
            'n_estimators': scope.int(hp.quniform('n_estimators', 500, 5000, 100)),
            'min_child_samples': scope.int(hp.quniform('min_child_samples', 20, 500, 5)),
            'subsample': hp.quniform('subsample', 0.5, 0.95, 0.05),
            'colsample_bytree': hp.quniform('colsample_bytree', 0.5, 1.0, 0.05),
            'reg_alpha': hp.qloguniform('reg_alpha', np.log(1e-8), np.log(10.0), 0.01),
            'reg_lambda': hp.qloguniform('reg_lambda', np.log(1e-8), np.log(10.0), 0.01),
            'min_split_gain': hp.qloguniform('min_split_gain', np.log(1e-8), np.log(1.0), 0.01),
            'boosting_type': hp.choice('boosting_type', ['gbdt', 'dart', 'goss']),
            'objective':hp.choice('objective',['regression','huber','fair'])
        }
        self.search_choice = {
            'boosting_type':['gbdt', 'dart', 'goss'],
            'objective':['regression','huber','fair','gamma']
        }
        self.params = { # basic params
            'n_estimators':3000,
            'objective':'regression',
            'boosting_type':'gbdt',
        }
        self.model = self.define_model()

    def define_model(self):
        return LGBMRegressor(
            **self.params,
            metric='rmse',
            random_state=self.random_seed,
            n_jobs=-1,
        )

    def hyperparam_tuning(self):
        def objective(params):
            params['num_leaves'] = int(params['num_leaves'])
            params['max_depth'] = int(params['max_depth'])
            params['n_estimators'] = int(params['n_estimators'])
            params['min_child_samples'] = int(params['min_child_samples'])

            model = LGBMRegressor(
                **params,
                metric='rmse',
                random_state=self.random_seed,
                n_jobs=-1,
            )

            # cross-validation
            kf = KFold(n_splits=3, shuffle=True, random_state=self.random_seed)
            scores = []
            for train_idx, val_idx in kf.split(self.train_dataset.features):
                X_tr, X_val = self.train_dataset.features[train_idx], self.train_dataset.features[val_idx]
                y_tr, y_val = self.train_dataset.target[train_idx], self.train_dataset.target[val_idx]
                model.fit(
                    X_tr, y_tr,
                    eval_set=[(X_tr,y_tr), (X_val, y_val)],
                    eval_metric='rmse',
                    callbacks=[
                        lgb.early_stopping(stopping_rounds=self.early_stopping_rounds)
                    ]
                )
                preds = model.predict(X_val)
                rmse = root_mean_squared_error(y_val, preds)
                scores.append(rmse)
            return {'loss':np.mean(scores), 'status':STATUS_OK}
        trials = Trials()
        best = fmin(
            fn=objective,
            space=self.search_space,
            algo=tpe.suggest,
            max_evals=10,
            trials=trials,
            rstate=np.random.default_rng(self.random_seed)
        )
        # best param으로 업데이트
        self.params = {
            'num_leaves':int(best['num_leaves']),
            'max_depth':int(best['max_depth']),
            'learning_rate':float(best['learning_rate']),
            'n_estimators': int(best['n_estimators']),
            'min_child_samples':int(best['min_child_samples']),
            'subsample': float(best['subsample']),
            'colsample_bytree': float(best['colsample_bytree']),
            'reg_alpha': float(best['reg_alpha']),
            'reg_lambda': float(best['reg_lambda']),
            'min_split_gain':float(best['min_split_gain']),
            'boosting_type':self.search_choice.get('boosting_type')[best['boosting_type']],
            'objective':self.search_choice.get('objective')[best['objective']],
        }
        # best_param으로 다시 모델 정의
        self.model = self.define_model()

    def train(self):
        self.model.fit(
            self.train_dataset.features, self.train_dataset.target,
            eval_metric='rmse'
        )

    def validate(self):
        if self.val_dataset is None:
            raise ValueError("There is no validation dataset!")
        self.train()
        val_preds = self.model.predict(self.val_dataset.features)
        val_rmse = root_mean_squared_error(self.val_dataset.target, val_preds)
        return val_rmse
