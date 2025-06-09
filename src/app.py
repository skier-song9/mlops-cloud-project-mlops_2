from flask import Flask
from flask import request, g, copy_current_request_context, send_file, jsonify # session,
# session은 각 클라이언트별로 json 형태의 데이터를 독립적으로 관리할 수 있는 객체이다.
# g 객체는 json 형태의 데이터가 아니더라도 클라이언트별로 독립적으로 관리할 수 있도록 해준다.
from flask import render_template #템플릿 파일(.html) 서비스용
from flask import make_response #응답 객체(Response) 생성용
from flask import flash, redirect #응답메시지 및 리다이렉트용
from flask import jsonify #JSON형태의 문자열로 응답시
from flask_cors import CORS

import os, re, time
import json
from dotenv import load_dotenv
import sys
import logging

sys.path.append(
    os.path.dirname( # /project_root
        os.path.dirname( # /project_root/src
            os.path.abspath(__file__) # /project_root/src/webapp.py
        )
    )
)
from src.utils.utils import project_path, get_current_time, get_local_ip
from src.dataset.data_process import AptDataset, read_remote_dataset, apt_preprocess
from src.inference.inference import get_inference_dataframe, plot_prediction

log_dir = os.path.join(project_path(), 'weblogs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f'uvicorn_{get_current_time(strformat="%y%m%d%H%M")}.log')
# 로거 설정
logging.getLogger('waitress')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8')
    ]
)

# 웹 앱 생성
app = Flask(__name__, # app
    template_folder=os.path.join(project_path(),'src','assets'),
    static_folder=os.path.join(project_path(),'src','assets'))

#CORS에러 처리
CORS(app)

#브라우저로 바로 JSON 응답시 한글 처리(16진수로 URL인코딩되는 거 막기)
#Response객체로 응답시는 생략(내부적으로 utf8을 사용)
app.config['JSON_AS_ASCII']=False

# server의 ROOT URL
APP_ROOT = os.path.join(project_path(),'src') # /project_path/src

# 필요 변수들
ASSETS = os.path.join(APP_ROOT,'assets')
# load .env
load_dotenv(os.path.join(project_path(),'.env'))
KAKAO_JS_KEY = os.getenv("KAKAO_JS_KEY")

@app.route('/')
def index():
    return render_template('index.html', kakao_app_key=KAKAO_JS_KEY)

@app.route('/inference')
def inference():
    lat = request.args.get('lat')
    lng = request.args.get('lng')
    roadname = request.args.get('roadname')
    lat, lng = float(lat), float(lng)

    # ### 이미 추론을 했던 아파트라면 기존의 추론 파일을 사용
    # current_time = get_current_time(strformat="%y%m%d")
    # savedir = os.path.join(project_path(), 'src', 'assets', 'plots', current_time)
    # os.makedirs(savedir, exist_ok=True)
    # savepath = os.path.join(savedir, f'{roadname.replace(" ", "_")}.png')
    # if not os.path.exist(savepath):
    #     # load processed dataset from S3
    #     print("✅ start S3_APT_PROCESSED download")
    #     yesterday_datetime = get_current_time(strformat="%y%m%d", timedeltas=1)
    #     s3_url = os.getenv("S3_APT_PROCESSED").replace(".csv",f"_{yesterday_datetime}.csv")
    #     apt = read_remote_dataset(filepath=s3_url)
    #     print("✅ S3_APT_PROCESSED download finished")

    #     # get scaler, encoder
    #     full_dataset = AptDataset(
    #         df=apt, scaler="No", encoders=dict()
    #     )
    #     scaler, encoders = full_dataset.scaler, full_dataset.encoders

    #     # get_inference_dataframe
    #     selected_df = get_inference_dataframe(apt_process, lat, lng)
    #     isApprox = 0 if selected_df.shape[0] < 92 else 1

    #     # mlflow 에서 모델 로드
    #     try:
    #         model = mlflow.pyfunc.load_model("models:/[???]/Production")
    #     except Exception as e:
    #         print(f"⚠️ mlflow 모델 로드 실패: {e}")
    #     # model prediction
    #     inference_features = selected_df.drop(columns=['datetime'],axis=1)
    #     preds = model.predict(inference_features)
    #     selected_df['target'] = preds
    #     savepath = plot_prediction(selected_df, savepath)

    # savepath = savepath.split("/src")[-1] # web에 맞게 경로 수정
    # return jsonify({"image_url": savepath, 'isApprox': isApprox})

    ### ✅ 테스트용 이미지
    image_url = '/assets/plots/250608/lotte.png'
    return jsonify({'image_url': image_url, 'isApprox': 1})

if __name__ == '__main__':
    from waitress import serve
    local_ip = get_local_ip()
    print(f"Running on http://{local_ip}:8080")
    serve(app=app, host=local_ip, port=8080)
