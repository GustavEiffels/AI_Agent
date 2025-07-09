import OpenDartReader
from dotenv import load_dotenv
import os
import pandas as pd
from datetime import datetime

load_dotenv()

api_key = os.getenv("DART_KEY")

if api_key is None:
    print("오류: DART_KEY 환경 변수를 찾을 수 없습니다. .env 파일을 확인해주세요.")
    exit()

try:
    dart = OpenDartReader(api_key)
except Exception as e:
    print(f"OpenDartReader 초기화 중 오류 발생: {e}")
    print("API 키가 유효한지 확인하거나, OpenDartReader 라이브러리 설치 상태를 확인해주세요.")
    exit()

company_name = "삼성전자" 

corp_code = None
listing_status = "정보 없음"

try:
    samsung_corp_info = dart.list(company_name)

    if samsung_corp_info is not None and not samsung_corp_info.empty:
        filtered_corp = samsung_corp_info[samsung_corp_info['corp_name'] == company_name]

        if not filtered_corp.empty:
            corp_code = filtered_corp.iloc[0]['corp_code']
            corp_cls = filtered_corp.iloc[0]['corp_cls'] # 법인구분 (Y:유가, K:코스닥, N:코넥스, E:기타)

            if corp_cls == 'Y':
                listing_status = "상장 (유가증권시장)"
            elif corp_cls == 'K':
                listing_status = "상장 (코스닥시장)"
            elif corp_cls == 'N':
                listing_status = "상장 (코넥스시장)"
            elif corp_cls == 'E':
                listing_status = "비상장 (기타법인)"
            else:
                listing_status = "상장 여부 불명"
        else:
            print(f"'{company_name}'에 대한 정확한 기업 정보를 찾을 수 없습니다. 검색 결과는 있으나 이름이 불일치합니다.")
    else:
        print(f"'{company_name}'에 대한 기업 정보를 찾을 수 없습니다. DART API 호출 실패 또는 검색 결과 없음.")

except Exception as e:
    print(f"기업 정보 조회 중 오류 발생: {e}")

if corp_code is None:
    print("기업 고유번호를 얻지 못하여 재무 데이터 조회를 진행할 수 없습니다.")
    exit()


current_year = datetime.now().year
current_month = datetime.now().month
current_day = datetime.now().day

latest_quarter_year = current_year
latest_quarter_code = None
latest_quarter_info = None

if current_month >= 8 and current_day >= 14: 
    latest_quarter_code = '11012' 
    latest_quarter_info = f"{current_year}년 2분기"
elif current_month >= 5: 
    latest_quarter_code = '11013' 
    latest_quarter_info = f"{current_year}년 1분기"
else: 
    latest_quarter_year = current_year - 1
    latest_quarter_code = '11011' 
    latest_quarter_info = f"{current_year - 1}년 4분기"

previous_year_same_quarter_year = latest_quarter_year - 1
previous_year_same_quarter_code = latest_quarter_code
previous_year_same_quarter_info = f"{previous_year_same_quarter_year}년 {latest_quarter_info.split('년 ')[1]}"


reprt_code = ['11013', '11012', '11014', '11011']

def convert(data):
    result = int(df1.loc[data].iloc[0]['thstrm_amount'])
    print(f'data : {result}')


df1 = pd.DataFrame(dart.finstate_all('삼성전자', 2024, reprt_code='11013', fs_div='CFS')) 
asset_moveable   = (df1.sj_nm == '재무상태표') & (df1.account_nm == '유동자산')
asset_unmoveable = (df1.sj_nm == '재무상태표') & (df1.account_nm == '비유동자산')
bet_moveable     = (df1.sj_nm == '재무상태표') & (df1.account_nm == '유동부채')
bet_unmoveable   = (df1.sj_nm == '재무상태표') & (df1.account_nm == '비유동부채')
amount_bet       = (df1.sj_nm == '재무상태표') & (df1.account_nm == '부채총계')
amount_asset     = (df1.sj_nm == '재무상태표') & ((df1.account_nm == '자본총계') | (df1.account_nm == '반기말자본') | (df1.account_nm == '3분기말자본') | (df1.account_nm == '분기말자본') | (df1.account_nm == '1분기말자본'))  
revenue          = ((df1.sj_nm == '손익계산서') | (df1.sj_nm == '포괄손익계산서')) & ((df1.account_nm == '매출액') | (df1.account_nm == '수익(매출액)'))
gross_profit     = ((df1.sj_nm == '손익계산서') | (df1.sj_nm == '포괄손익계산서')) & (df1.account_nm == '매출총이익')
operating_income = ((df1.sj_nm == '손익계산서') | (df1.sj_nm == '포괄손익계산서')) & ((df1.account_nm == '영업이익(손실)') | (df1.account_nm == '영업이익'))
net_income       = ((df1.sj_nm == '손익계산서') | (df1.sj_nm == '포괄손익계산서')) & \
                                ((df1.account_nm == '당기순이익(손실)') | (df1.account_nm == '당기순이익') | \
                                (df1.account_nm == '분기순이익') | (df1.account_nm == '분기순이익(손실)') | (df1.account_nm == '반기순이익') | (df1.account_nm == '반기순이익(손실)') | \
                                (df1.account_nm == '연결분기순이익') | (df1.account_nm == '연결반기순이익')| (df1.account_nm == '연결당기순이익')|(df1.account_nm == '연결분기(당기)순이익')|(df1.account_nm == '연결반기(당기)순이익')|\
                                (df1.account_nm == '연결분기순이익(손실)'))

convert(asset_moveable)
convert(asset_unmoveable)
convert(bet_moveable)
convert(bet_unmoveable)

convert(revenue)
convert(gross_profit)
convert(operating_income)
convert(net_income)

convert(amount_bet)
convert(amount_asset)