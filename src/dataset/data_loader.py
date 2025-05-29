import pandas as pd
import fire
import requests
from tqdm import tqdm
import io
from dotenv import load_dotenv
import os

class S3PublicCSVDownloader:
    def download_csv(self,
                     url: str = None,
                     output_filename: str = None):
        
        """
        퍼블릭 S3 URL에서 CSV 파일을 다운로드하고, 진행률을 표시하며 로컬에 저장합니다.
        URL과 파일명은 .env에서 불러옵니다.
        """

        load_dotenv()

        # .env에서 기본값 불러오기
        url = os.getenv("S3_URL")
        output_filename = os.getenv("OUTPUT_FILENAME", "apt_local_copy.csv")

        if not url:
            print("[ERROR] URL이 제공되지 않았습니다. .env에 S3_URL을 설정하세요.")
            return
        print(f"[INFO] 다운로드 시작: {url}")

        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))

            chunk_size = 1024  # 1KB씩 다운로드
            buffer = io.BytesIO()

            with tqdm(total=total_size, unit='B', unit_scale=True, desc="Downloading") as pbar:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    buffer.write(chunk)
                    pbar.update(len(chunk))

            buffer.seek(0)  # 메모리 포인터 처음으로
            df = pd.read_csv(buffer)
            df.to_csv(output_filename, index=False)

            print(f"[SUCCESS] 다운로드 및 저장 완료: {output_filename} (rows: {len(df)})")

        except Exception as e:
            print(f"[ERROR] 다운로드 실패: {e}")

if __name__ == "__main__":
    fire.Fire(S3PublicCSVDownloader)
