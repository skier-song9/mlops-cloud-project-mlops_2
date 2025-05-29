import os
import sys

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd
from catboost import CatBoostRegressor
from dotenv import load_dotenv

from src.dataset.getdatav2 import get_data_main #save_alldata_to_s3
from src.utils.utils import project_path

load_dotenv(dotenv_path=f"{project_path()}/.env", override=True)
serviceKey = os.environ["APIKey"] 

def train_model(path):
    df = pd.read_csv(path)
    
    selected_cols = ['aptNm','buildYear','dealYear', 'dealMonth', 
                    'dealAmount','floor','umdNm','excluUseAr']
    train_df = df[selected_cols].copy()  
    
    train_df = train_df.rename(columns={'dealAmount':'target'})
    train_df['target'] = train_df['target'].str.replace(',', "").astype(int)
    
    X_train = train_df.drop('target', axis=1)
    y_train = train_df['target']
    
    os.makedirs('/Users/hoppure/dev/mlops/data/tmp/catboost_info', exist_ok=True)

    model = CatBoostRegressor(
        iterations=100,
        depth=3,
        learning_rate=0.1,
        loss_function='RMSE',
        verbose=0,
        train_dir='/Users/hoppure/dev/mlops/data/tmp/catboost_info'  # ✅ 절대 경로 지정

    )
    
    cat_features = ['aptNm', 'umdNm']
    model.fit(X_train, y_train, cat_features=cat_features)


# ✅ get_data_main을 래핑 (Airflow는 파라미터 없는 함수만 직접 사용 가능)
def airflow_get_data_main():
    # 필요하다면 start, end 파라미터를 하드코딩하거나 환경변수로 받으세요.
    path = get_data_main(start=200701, end=None)
    return path

def airflow_train_model(ti):
    path = ti.xcom_pull(task_ids='get_data')
    train_model(path)

""" 작성중
def airflow_save_alldata_to_s3():
    save_alldata_to_s3()
"""

with DAG(
    dag_id="apt_price_prediction",
    start_date=datetime(2023, 1, 1),
    schedule="@daily",
    catchup=False,
) as dag:
    
    get_data_task = PythonOperator(
        task_id="get_data",
        python_callable=airflow_get_data_main
    )
    
    preprocessing_task = PythonOperator(
        task_id="preprocess_data",  # ✅ 올바른 task_id
        python_callable=airflow_train_model
    )

    # get_data_task가 끝나고 preprocessing_task가 실행되도록 설정
    get_data_task >> preprocessing_task


if __name__ == '__main__':
    print(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
          )