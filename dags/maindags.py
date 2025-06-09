from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from datetime import datetime, timedelta

# # 공유 볼륨 설정
# shared_mount = Mount(
#     target='/shared_data',
#     source='/tmp/airflow_shared',
#     type='bind'
# )

# 각 DockerOperator에 mounts=[shared_mount] 추가


default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2025, 6, 5),
}

with DAG(
    dag_id='main_py_pipeline',
    default_args=default_args,
    schedule=None,
    catchup=False,
    description='Run get_data, geoprocess, preprocess in sequence using DockerOperator'
) as dag:

    get_data = DockerOperator(
        task_id='get_data',
        image='mloops:latest',
        command='python main.py get_data --start 202506',
        working_dir='/root/mlops/src',  # ✅ 올바른 경로로 수정
        network_mode='bridge',
        # mount=[shared_mount],
        auto_remove='success',  # ✅ 'never' 대신 'success' 권장
        docker_url='unix://var/run/docker.sock',
    )

    geoprocess = DockerOperator(
        task_id='geoprocess',
        image='mloops:latest',
        command='python main.py geoprocess',
        working_dir='/root/mlops/src',  # ✅ 올바른 경로로 수정
        network_mode='bridge',
        # mount=[shared_mount],
        auto_remove='success',
        docker_url='unix://var/run/docker.sock',
    )

    preprocess = DockerOperator(
        task_id='preprocess',
        image='mloops:latest',
        command='python main.py preprocess',
        working_dir='/root/mlops/src',  # ✅ 올바른 경로로 수정
        network_mode='bridge',
        # mount=[shared_mount],
        auto_remove='success',
        docker_url='unix://var/run/docker.sock',
    )

    get_data >> geoprocess >> preprocess
