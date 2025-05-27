import time

import requests
import xmltodict
import pandas as pd


def fetch_apt_trade_data(service_key, lawd_cd, deal_ymd, num_of_rows=1000, page_no=1):
    """
    국토교통부 아파트 매매 실거래가 상세자료 API에서 데이터 1페이지 조회
    """
    url = 'http://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev'
    params = {
        "serviceKey": service_key,
        "LAWD_CD": lawd_cd,
        "DEAL_YMD": deal_ymd,
        "numOfRows": num_of_rows,
        "pageNo": page_no,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = xmltodict.parse(response.text)
    return data


def collect_all_pages(service_key, lawd_cd, deal_ymd, sleep_sec=0.5):
    """
    한 지역, 한 달의 모든 페이지 데이터 수집
    """
    all_items = []
    page_no = 1
    while True:
        data = fetch_apt_trade_data(service_key, lawd_cd, deal_ymd, page_no=page_no)
        items = data['response']['body']['items']
        if not items or 'item' not in items:
            break
        page_items = items['item']
        if isinstance(page_items, dict):  # 단일 거래만 있을 때
            page_items = [page_items]
        all_items.extend(page_items)
        total_count = int(data['response']['body']['totalCount'])
        if len(all_items) >= total_count:
            break
        page_no += 1
        time.sleep(sleep_sec)  # API 과다 호출 방지
    return all_items


def items_to_dataframe(items):
    return pd.DataFrame(items)


def get_ymd_list(start:int, end:int):
    """
    년월 두개를 입력하면 그 사이의 년월을 리스트로 반환
    ** 예외처리 안되어 있음 **
    ex (202003, 202008) 입력 
    [202003, 202004, 202005, 202006, 202007, 202008]
    """
    start_year = int(str(start)[:4])
    start_month = int(str(start)[4:6])
    end_year = int(str(end)[:4])
    end_month = int(str(end)[4:6])

    months = []
    year, month = start_year, start_month
    while (year < end_year) or (year == end_year and month <= end_month):
        months.append(year * 100 + month)
        # 다음 달로 이동
        month += 1
        if month > 12:
            month = 1
            year += 1
    return months


def get_from_date(service_key, lawd_cd, start:int, end:int):
    """
    한 지역, 입력된 년월의 모든 페이지 데이터 수집
    """
    all_items = []
    deal_ymds = get_ymd_list(start, end)
    for deal_ymd in deal_ymds:
        items = collect_all_pages(service_key, lawd_cd, deal_ymd)
        all_items.extend(items)
    return all_items


def get_all_lawd_cd(service_key, lawd_cds:list, start:int, end:int):
    """
    반복문으로 입력된 년 월의 모든 페이지 데이터 수집
    """
    all_items = []
    deal_ymds = get_ymd_list(start, end)
    for lawd_cd in lawd_cds:
        for deal_ymd in deal_ymds:
            items = collect_all_pages(service_key, lawd_cd, deal_ymd)
            all_items.extend(items)
    return all_items

'''
# working
def add_new_data():
    pass
'''

if __name__ == "__main__":
    
    from dotenv import load_dotenv

    load_dotenv()

    serviceKey = os.environ["APIKey"] 

    lawd_cds = [ # 서울 구별 법정동코드 모음
                11110, 
                11140,
                11170,
                11200,
                11215,
                11230,
                11260,
                11290,
                11305,
                11320,
                11350,
                11380,
                11410,
                11440,
                11470,
                11500,
                11530,
                11545,
                11560,
                11590,
                11620,
                11650,
                11680,
                11710,
                11740
                ]

    start = 200701  # 시작년월, 형식 딱 이렇게 넣기
    end = 202505  # 마지막년월
    
    data = get_all_lawd_cd(serviceKey,lawd_cds, start, end)
    df = items_to_dataframe(data)
    # print(df)
    df.to_csv("apt_trade_data1.csv", index=False)
