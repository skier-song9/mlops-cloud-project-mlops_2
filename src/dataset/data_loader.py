import boto3
import pandas as pd
import io
import os
import fire


class S3DataSaver:
    def download_csv(self, bucket_name, object_key, output_path, aws_profile=None):
        """
        S3에서 데이터를 받아 CSV로 저장합니다.

        Args:
            bucket_name (str): S3 버킷 이름
            object_key (str): S3 내부 경로 (예: 'data/apt_trade_data.csv')
            output_path (str): 저장할 CSV 경로 (예: '/shared_data/raw_data.csv')
            aws_profile (str, optional): AWS 프로파일 이름 (도커 외부에서 테스트할 때 사용)
        """

        # AWS 세션 설정
        if aws_profile:
            session = boto3.Session(profile_name=aws_profile)
        else:
            # 도커 환경에서는 환경변수로 인증함
            session = boto3.Session()

        s3 = session.client("s3")

        # 객체 가져오기
        print(f"Downloading s3://{bucket_name}/{object_key} ...")
        obj = s3.get_object(Bucket=bucket_name, Key=object_key)
        df = pd.read_csv(io.BytesIO(obj['Body'].read()))

        # 디렉토리 없으면 생성
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # CSV 저장
        df.to_csv(output_path, index=False)
        print(f"Saved to {output_path}")


if __name__ == '__main__':
    fire.Fire(S3DataSaver)
