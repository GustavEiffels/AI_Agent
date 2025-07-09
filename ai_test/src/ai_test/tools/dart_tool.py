import OpenDartReader
from dotenv import load_dotenv
import os
import pandas as pd
from datetime import datetime

load_dotenv()
api_key = os.getenv("DART_KEY")


def get_financial_quarters_info(current_date=None):

    if current_date is None:
        current_date = datetime.now()

    current_year = current_date.year
    current_month = current_date.month
    current_day = current_date.day

    latest_quarter = {'year': None, 'code': None, 'info': None, 'q_num': None} 

    if current_month < 5 or (current_month == 5 and current_day < 15):
        latest_quarter['year'] = current_year - 1
        latest_quarter['code'] = '11011'
        latest_quarter['info'] = f"{current_year - 1}년 4분기"
        latest_quarter['q_num'] = 4
    elif current_month < 8 or (current_month == 8 and current_day < 14):
        # 5월 15일 ~ 8월 13일: 현재 연도 1분기보고서(Q1)가 최신
        latest_quarter['year'] = current_year
        latest_quarter['code'] = '11013'
        latest_quarter['info'] = f"{current_year}년 1분기"
        latest_quarter['q_num'] = 1
    elif current_month < 11 or (current_month == 11 and current_day < 14):
        # 8월 14일 ~ 11월 13일: 현재 연도 반기보고서(Q2)가 최신
        latest_quarter['year'] = current_year
        latest_quarter['code'] = '11012'
        latest_quarter['info'] = f"{current_year}년 2분기"
        latest_quarter['q_num'] = 2
    else: # current_month >= 11 and current_day >= 14 or current_month == 12
        # 11월 14일 ~ 12월 31일: 현재 연도 3분기보고서(Q3)가 최신
        latest_quarter['year'] = current_year
        latest_quarter['code'] = '11014'
        latest_quarter['info'] = f"{current_year}년 3분기"
        latest_quarter['q_num'] = 3

    # 2. '최근 분기 직전 분기' 계산
    previous_quarter = {'year': None, 'code': None, 'info': None}
    if latest_quarter['q_num'] == 1:
        previous_quarter['year'] = latest_quarter['year'] - 1
        previous_quarter['code'] = '11011' # 전년도 4분기 (사업보고서)
        previous_quarter['info'] = f"{previous_quarter['year']}년 4분기"
    elif latest_quarter['q_num'] == 2:
        previous_quarter['year'] = latest_quarter['year']
        previous_quarter['code'] = '11013' # 1분기
        previous_quarter['info'] = f"{previous_quarter['year']}년 1분기"
    elif latest_quarter['q_num'] == 3:
        previous_quarter['year'] = latest_quarter['year']
        previous_quarter['code'] = '11012' # 2분기 (반기)
        previous_quarter['info'] = f"{previous_quarter['year']}년 2분기"
    elif latest_quarter['q_num'] == 4: # 사업보고서가 최신 분기인 경우
        previous_quarter['year'] = latest_quarter['year']
        previous_quarter['code'] = '11014' # 3분기
        previous_quarter['info'] = f"{previous_quarter['year']}년 3분기"


    # 3. '최근 분기 1년 전 동일 분기' 계산
    previous_year_same_quarter = {'year': None, 'code': None, 'info': None}
    previous_year_same_quarter['year'] = latest_quarter['year'] - 1
    previous_year_same_quarter['code'] = latest_quarter['code']
    previous_year_same_quarter['info'] = f"{previous_year_same_quarter['year']}년 {latest_quarter['info'].split('년 ')[1]}"


    return {
        'latest_quarter': latest_quarter,
        'previous_quarter': previous_quarter,
        'previous_year_same_quarter': previous_year_same_quarter
    }

def convert(data):
    return int(df1.loc[data].iloc[0]['thstrm_amount'])


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
corp_cls = ''

try:
    samsung_corp_info = dart.list(company_name)

    if samsung_corp_info is not None and not samsung_corp_info.empty:
        filtered_corp = samsung_corp_info[samsung_corp_info['corp_name'] == company_name]

        if not filtered_corp.empty:
            corp_code = filtered_corp.iloc[0]['corp_code']
            corp_cls = filtered_corp.iloc[0]['corp_cls'] 

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


q_data = get_financial_quarters_info()

print(f"q_data.latest_quarter.code : {q_data['latest_quarter']['code']} - {q_data['latest_quarter']['year']}")
print(f"q_data.previous_quarter.code : {q_data['previous_quarter']['code']} - {q_data['previous_quarter']['year']}")
print(f"q_data.previous_year_same_quarter.code : {q_data['previous_year_same_quarter']['code']} - {q_data['previous_year_same_quarter']['year']}")


result_json = {}

for q_key, data in q_data.items():
    code = data['code']
    year = data['year']

    df1 = pd.DataFrame(dart.finstate_all(company_name, year, reprt_code=code, fs_div='CFS')) 
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
    result_json[q_key] = {
        'asset_moveable':convert(asset_moveable),
        'asset_unmoveable':convert(asset_unmoveable),
        'bet_moveable':convert(bet_moveable),
        'bet_unmoveable':convert(bet_unmoveable),
        'amount_bet':convert(amount_bet),
        'amount_asset':convert(amount_asset),
        'revenue':convert(revenue),
        'gross_profit':convert(gross_profit),
        'operating_income':convert(operating_income),
        'net_income':convert(net_income)
    }


print(f'result_json : {result_json}')