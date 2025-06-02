#!/bin/bash
set -e 

# username 인자 체크
if [ -z "$1" ]; then
  echo "Usage: docker run <image> <github-username>"
  exit 1
fi

USERNAME=$1

# git clone (이미 있을 경우 재클론 방지)
if [ ! -d "/mlops-cloud-project-mlops_2" ]; then
  git clone https://github.com/${USERNAME}/mlops-cloud-project-mlops_2.git
  cd /mlops-cloud-project-mlops_2
  git config --global credential.helper store
  git config --global core.pager "cat"
  git config --global core.editor "vim"
  git remote add upstream https://github.com/AIBootcamp13/mlops-cloud-project-mlops_2.git
  git remote set-url --push upstream no-push
fi

# selenium 사용을 위해 google chrome 설치
if [ ! -d "/mlops-cloud-project-mlops_2" ]; then
  cd ..
  # 최신 stable 버전의 구글 크롬 드라이버 다운로드
  wget wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
  apt-get update
  apt install -y vim
  apt-get install -y ./google-chrome-stable_current_amd64.deb
  cd /mlops-cloud-project-mlops_2
fi

# requirements.txt 설치
if [ -f "requirements.txt" ]; then
  pip install --no-cache-dir -r requirements.txt
fi

# bash로 컨테이너 실행
exec bash