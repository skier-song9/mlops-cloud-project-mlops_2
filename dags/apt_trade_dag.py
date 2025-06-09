from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2025, 6, 5),
}
with DAG(
    dag_id='main_py_pipeline',
    default_args=default_args,
    schedule_interval=None, # 필요시 변경 timedelta(days=1),
    catchup=False,
    description='Run get_data, geoprocess, preprocess in sequence using DockerOperator'
    ) as dag:
        get_data = DockerOperator(
        task_id='get_data',
        image='mloops:latest', # main.py가 포함된 이미지 이름
        command='python main.py get_data',
        working_dir='/mlops/src',       # main.py가 위치한 컨테이너 내 경로
        network_mode='bridge',
        auto_remove=True,
        docker_url='unix://var/run/docker.sock',
        environment={
        # 필요하다면 환경변수 지정
    },
    mounts=[
        # 필요하다면 볼륨 마운트 예시:
        # Mount(source='/host/path', target='/app', type='bind')
    ]
)
geoprocess = DockerOperator(
    task_id='geoprocess',
    image='mloops:latest',
    command='python main.py geoprocess',
    working_dir='/mlops/src',
    network_mode='bridge',
    auto_remove=True,
    docker_url='unix://var/run/docker.sock',
)
preprocess = DockerOperator(
    task_id='preprocess',
    image='mloops:latest',
    command='python main.py preprocess',
    working_dir='/mlops/src',
    network_mode='bridge',
    auto_remove=True,
    docker_url='unix://var/run/docker.sock',
)
# 태스크 순서 지정 (get_data → geoprocess → preprocess)
get_data >> geoprocess >> preprocess