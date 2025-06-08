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
from src.utils.utils import project_path, get_current_time

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
    lat, lng = float(lat), float(lng)

    ### ✅ 테스트용 이미지
    image_url = '/assets/plots/250608/lotte.png'
    return jsonify({'image_url': image_url})



if __name__ == '__main__':
    from waitress import serve
    serve(app=app, host="0.0.0.0", port=8080)
