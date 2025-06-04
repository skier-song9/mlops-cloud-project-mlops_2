import os
import random
import datetime
from zoneinfo import ZoneInfo

import numpy as np


def init_seed():
    np.random.seed(42)
    random.seed(42)


def project_path():
    return os.path.join(
        os.path.dirname(  # /opt/mlops/src/utils
            os.path.abspath(__file__)  # /opt/mlops/src/utils/utils.py
        ),
        "..",  # /opt/mlops/src
        ".."   # /opt/mlops  -> project_path
    )


def model_dir(model_name):
    return os.path.join(
        project_path(),  # /opt/mlops
        "models",        # /opt/mlops/models
        model_name       # /opt/mlops/models/{model_name}
    )


def auto_increment_run_suffix(name: str, pad=3):
    suffix = name.split("-")[-1]
    next_suffix = str(int(suffix) + 1).zfill(pad)
    return name.replace(suffix, next_suffix)

def get_current_time(strformat='%y%m%d%H%M%S'):
    kst = ZoneInfo("Asia/Seoul")
    current_time = datetime.datetime.now(kst).strftime(strformat)
    return current_time

def download_dir():
    return os.path.join(
        project_path(),
        'src',
        'data'
    )