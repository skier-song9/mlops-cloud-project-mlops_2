import os
import sys
import glob
import re
import joblib

sys.path.append(
    os.path.dirname( # /mlops/
        os.path.dirname(  # /mlops/src
            os.path.abspath(__file__)  # /mlops/src/main.py
        )
    )
)

import numpy as np
import pandas as pd

from src.utils.utils import model_dir
from src.model.model_cards import LGBMRegressorCard
from src.dataset.data_process import AptDataset

def load_checkpoint(model_name):
    assert model_name in ['LGBMRegressor']
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
        bundle = joblib.load('model_bundle.pkl')

        model = bundle['model']
        scaler = bundle['scaler']
        val_loss = bundle['val_loss']
        encoders = bundle['encoders']
    return model, scaler, val_loss, encoders

def get_inference_dataset():
    pass