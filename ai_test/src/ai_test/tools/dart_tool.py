import os
import pandas as pd
from typing import Type
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import OpenDartReader
from datetime import datetime

load_dotenv()

# 🔹 퀘터 정보 구하기 함수 그대로 사용
def get_financial_quarters_info(current_date=None):
    if current_date is None:
        current_date = datetime.now()

    current_year = current_date.year
    current_month = current_date.month
    current_day = current_date.day

    latest_quarter = {'year': None, 'code': None, 'info': None, 'q_num': None} 

    if current_month < 5 or (current_month == 5 and current_day < 15):
        latest_quarter.update({'year': current_year - 1, 'code': '11011', 'info': f"{current_year - 1}년 4분기", 'q_num': 4})
    elif current_month < 8 or (current_month == 8 and current_day < 14):
        latest_quarter.update({'year': current_year, 'code': '11013', 'info': f"{current_year}년 1분기", 'q_num': 1})
    elif current_month < 11 or (current_month == 11 and current_day < 14):
        latest_quarter.update({'year': current_year, 'code': '11012', 'info': f"{current_year}년 2분기", 'q_num': 2})
    else:
        latest_quarter.update({'year': current_year, 'code': '11014', 'info': f"{current_year}년 3분기", 'q_num': 3})

    previous_quarter = {}
    if latest_quarter['q_num'] == 1:
        previous_quarter = {'year': latest_quarter['year'] - 1, 'code': '11011', 'info': f"{latest_quarter['year'] - 1}년 4분기"}
    elif latest_quarter['q_num'] == 2:
        previous_quarter = {'year': latest_quarter['year'], 'code': '11013', 'info': f"{latest_quarter['year']}년 1분기"}
    elif latest_quarter['q_num'] == 3:
        previous_quarter = {'year': latest_quarter['year'], 'code': '11012', 'info': f"{latest_quarter['year']}년 2분기"}
    elif latest_quarter['q_num'] == 4:
        previous_quarter = {'year': latest_quarter['year'], 'code': '11014', 'info': f"{latest_quarter['year']}년 3분기"}

    previous_year_same_quarter = {
        'year': latest_quarter['year'] - 1,
        'code': latest_quarter['code'],
        'info': f"{latest_quarter['year'] - 1}년 {latest_quarter['info'].split('년 ')[1]}"
    }

    return {
        'latest_quarter': latest_quarter,
        'previous_quarter': previous_quarter,
        'previous_year_same_quarter': previous_year_same_quarter
    }


# 🔹 값 추출 함수
def convert(df: pd.DataFrame, mask: pd.Series):
    try:
        return int(df.loc[mask].iloc[0]['thstrm_amount'])
    except Exception:
        return None

# 🔹 Pydantic 입력 스키마 정의
class FinancialDataInput(BaseModel):
    company_name: str = Field(..., description="조회할 기업의 정확한 이름 (예: LG전자)")

# 🔹 Custom Tool 정의
class CollectFinancialDataTool(BaseTool):
    name: str = "Collect Financial Data"
    description: str = (
        "기업 이름을 기반으로 OpenDART API에서 최신 3개 분기의 재무정보(매출, 이익, 자산, 부채 등)를 수집합니다."
    )
    args_schema: Type[BaseModel] = FinancialDataInput

    def _run(self, company_name: str) -> dict:
        api_key = os.getenv("DART_KEY")
        if api_key is None:
            raise ValueError("DART_KEY 환경 변수가 없습니다. .env 파일을 확인하세요.")

        dart = OpenDartReader(api_key)
        corp_info = dart.list(company_name)

        if corp_info is None or corp_info.empty:
            raise ValueError(f"{company_name}에 대한 기업 정보를 찾을 수 없습니다.")

        filtered = corp_info[corp_info['corp_name'] == company_name]
        if filtered.empty:
            raise ValueError(f"{company_name} 이름과 정확히 일치하는 기업 정보를 찾지 못했습니다.")

        q_data = get_financial_quarters_info()
        result_json = {}

        for q_key, data in q_data.items():
            code = data['code']
            year = data['year']

            try:
                df1 = pd.DataFrame(dart.finstate_all(company_name, year, reprt_code=code, fs_div='CFS'))
            except Exception as e:
                result_json[q_key] = {'error': f"{year} {code} 데이터 조회 실패: {str(e)}"}
                continue

            result_json[q_key] = {
                'asset_moveable':   convert(df1, (df1.sj_nm == '재무상태표') & (df1.account_nm == '유동자산')),
                'asset_unmoveable': convert(df1, (df1.sj_nm == '재무상태표') & (df1.account_nm == '비유동자산')),
                'bet_moveable':     convert(df1, (df1.sj_nm == '재무상태표') & (df1.account_nm == '유동부채')),
                'bet_unmoveable':   convert(df1, (df1.sj_nm == '재무상태표') & (df1.account_nm == '비유동부채')),
                'amount_bet':       convert(df1, (df1.sj_nm == '재무상태표') & (df1.account_nm == '부채총계')),
                'amount_asset':     convert(df1, (df1.sj_nm == '재무상태표') & (
                                            df1.account_nm.isin([
                                                '자본총계', '반기말자본', '3분기말자본', '분기말자본', '1분기말자본']))),
                'revenue':          convert(df1, (df1.sj_nm.isin(['손익계산서', '포괄손익계산서'])) & 
                                            df1.account_nm.isin(['매출액', '수익(매출액)'])),
                'gross_profit':     convert(df1, (df1.sj_nm.isin(['손익계산서', '포괄손익계산서'])) & 
                                            (df1.account_nm == '매출총이익')),
                'operating_income': convert(df1, (df1.sj_nm.isin(['손익계산서', '포괄손익계산서'])) & 
                                            df1.account_nm.isin(['영업이익(손실)', '영업이익'])),
                'net_income':       convert(df1, (df1.sj_nm.isin(['손익계산서', '포괄손익계산서'])) & 
                                            df1.account_nm.isin([
                                                '당기순이익(손실)', '당기순이익', '분기순이익', '분기순이익(손실)', 
                                                '반기순이익', '반기순이익(손실)', '연결분기순이익', '연결반기순이익',
                                                '연결당기순이익', '연결분기(당기)순이익', '연결반기(당기)순이익', '연결분기순이익(손실)'
                                            ]))
            }

        return result_json
