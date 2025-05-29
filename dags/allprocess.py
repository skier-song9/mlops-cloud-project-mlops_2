import os

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd
from catboost import CatBoostRegressor

def train_model():
    df = pd.read_csv("/Users/hoppure/dev/mlops/data/apt_trade_data.csv")
    
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

with DAG(
    dag_id="apt_price_prediction",
    start_date=datetime(2023, 1, 1),
    schedule_interval="@daily",
    catchup=False,
) as dag:
    
    preprocessing_task = PythonOperator(
        task_id="preprocess_data",  # ✅ 올바른 task_id
        python_callable=train_model  
    )
