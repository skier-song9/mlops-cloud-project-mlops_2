import pandas as pd
import fire
import requests
from tqdm import tqdm
import io

class S3PublicCSVDownloader:
    def download_csv(self,
                     url: str = "https://mloops2.s3.amazonaws.com/apt_trade_data.csv",
                     output_filename: str = "apt_local_copy.csv"):
        """
        퍼블릭 S3 URL에서 CSV 파일을 다운로드하고, 진행률을 표시하며 로컬에 저장합니다.

        Args:
            url (str): 퍼블릭 CSV 파일 URL (기본값: https://mloops2.s3.amazonaws.com/apt_trade_data.csv)
            output_filename (str): 로컬에 저장할 파일명 (기본값: apt_local_copy.csv)
        """
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
