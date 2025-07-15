import os, requests
import pandas as pd
from typing import Type
from dotenv import load_dotenv
import zipfile
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import OpenDartReader
from datetime import datetime
from io import BytesIO
from dateutil.relativedelta import relativedelta
load_dotenv()
import xml.etree.cElementTree as ET
import re



# 🔹 퀘터 정보 구하기 함수 그대로 사용
def get_financial_quarters_info(current_date=None):
    if current_date is None:
        current_date = datetime.now()

    current_year = current_date.year
    current_month = current_date.month
    current_day = current_date.day

    quarter_codes = {
        1: {'code': '11013', 'info_suffix': '1분기', 'cutoff_month': 5, 'cutoff_day': 15},
        2: {'code': '11012', 'info_suffix': '2분기', 'cutoff_month': 8, 'cutoff_day': 14},
        3: {'code': '11014', 'info_suffix': '3분기', 'cutoff_month': 11, 'cutoff_day': 14},
        4: {'code': '11011', 'info_suffix': '4분기', 'cutoff_month': 3, 'cutoff_day': 31}
    }

    latest_available_q_num = 0
    if (current_month > 5) or (current_month == 5 and current_day >= 15):
        latest_available_q_num = 1
    if (current_month > 8) or (current_month == 8 and current_day >= 14):
        latest_available_q_num = 2
    if (current_month > 11) or (current_month == 11 and current_day >= 14):
        latest_available_q_num = 3
    if (current_month < 5):
        if (current_month == 1 and current_day <= 15):
            pass
        latest_available_q_num = 4

    financial_quarters = []

    for q_num in range(1, latest_available_q_num + 1):
        if q_num == 4 and latest_available_q_num != 4:
            continue

        quarter_info = quarter_codes[q_num]
        year_to_use = current_year
        if q_num == 4:
            if current_month < quarter_info['cutoff_month'] or \
               (current_month == quarter_info['cutoff_month'] and current_day < quarter_info['cutoff_day']):
                continue

        financial_quarters.append({
            'year': year_to_use,
            'code': quarter_info['code'],
            'info': f"{year_to_use}년 {quarter_info['info_suffix']}",
            'q_num': q_num
        })

    years_to_cover = []

    previous_full_year = current_year - 1
    years_to_cover.append(previous_full_year)

    year_before_previous_full_year = current_year - 2
    years_to_cover.append(year_before_previous_full_year)

    for year in years_to_cover:
        for q_num in range(1, 5):
            quarter_info = quarter_codes[q_num]

            if {'year': year, 'code': quarter_info['code'], 'q_num': q_num} not in [{'year': q['year'], 'code': q['code'], 'q_num': q['q_num']} for q in financial_quarters]:
                 financial_quarters.append({
                    'year': year,
                    'code': quarter_info['code'],
                    'info': f"{year}년 {quarter_info['info_suffix']}",
                    'q_num': q_num
                })
    financial_quarters.sort(key=lambda x: (x['year'], x['q_num']))

    return {'all_quarters': financial_quarters}

# 🔹 값 추출 함수
def convert(df: pd.DataFrame, mask: pd.Series):
    try:
        return int(df.loc[mask].iloc[0]['thstrm_amount'])
    except Exception:
        return None

# 🔹 기업 존재 여부 확인
def company_name_exist(name:str)->dict:

    return_data = {
        'exist':True,
        'message':f'{name} Exist'
    }

    api_key = os.getenv("DART_KEY")
    if api_key is None:
        raise ValueError("DART_KEY 환경 변수가 없습니다. .env 파일을 확인하세요.")

    dart = OpenDartReader(api_key)
    try:
        corp_info = dart.list(name)
    except Exception as e:
        return_data['exist'] = False
        return_data['message'] = f'{name}에 대한 기업 정보를 찾을 수 없습니다.'
        return return_data

    if corp_info is None or corp_info.empty:
        return_data['exist'] = False
        return_data['message'] = f'{name}에 대한 기업 정보를 찾을 수 없습니다.'
        return return_data

    filtered = corp_info[corp_info['corp_name'] == name]

    if filtered.empty:
        return_data['exist'] = False
        return_data['message'] = f'{name}이름과 정확히 일치하는 기업 정보를 찾지 못했습니다.'

    return return_data

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

        corp_code = filtered.iloc[0]['corp_code']
        print(f'corp_code : {corp_code}')

        quarters_to_fetch  = get_financial_quarters_info()['all_quarters']
        result_json = {}

        data_success : bool = True

        for data in quarters_to_fetch:
            code  = data['code']
            year  = data['year']
            q_num = data['q_num']

            try:
                df1 = pd.DataFrame(dart.finstate_all(company_name, year, reprt_code=code, fs_div='CFS'))
                result_json[f'{year}_{q_num}'] = {
                    'asset_moveable': convert(df1, (df1.sj_nm == '재무상태표') & (df1.account_nm == '유동자산')),
                    'asset_unmoveable': convert(df1, (df1.sj_nm == '재무상태표') & (df1.account_nm == '비유동자산')),
                    'bet_moveable': convert(df1, (df1.sj_nm == '재무상태표') & (df1.account_nm == '유동부채')),
                    'bet_unmoveable': convert(df1, (df1.sj_nm == '재무상태표') & (df1.account_nm == '비유동부채')),
                    'amount_bet': convert(df1, (df1.sj_nm == '재무상태표') & (df1.account_nm == '부채총계')),
                    'amount_asset': convert(df1, (df1.sj_nm == '재무상태표') & (
                        df1.account_nm.isin([
                            '자본총계', '반기말자본', '3분기말자본', '분기말자본', '1분기말자본']))),
                    'revenue': convert(df1, (df1.sj_nm.isin(['손익계산서', '포괄손익계산서'])) &
                                       df1.account_nm.isin(['매출액', '수익(매출액)'])),
                    'gross_profit': convert(df1, (df1.sj_nm.isin(['손익계산서', '포괄손익계산서'])) &
                                            (df1.account_nm == '매출총이익')),
                    'operating_income': convert(df1, (df1.sj_nm.isin(['손익계산서', '포괄손익계산서'])) &
                                                df1.account_nm.isin(['영업이익(손실)', '영업이익'])),
                    'net_income': convert(df1, (df1.sj_nm.isin(['손익계산서', '포괄손익계산서'])) &
                                          df1.account_nm.isin([
                                              '당기순이익(손실)', '당기순이익', '분기순이익', '분기순이익(손실)',
                                              '반기순이익', '반기순이익(손실)', '연결분기순이익', '연결반기순이익',
                                              '연결당기순이익', '연결분기(당기)순이익', '연결반기(당기)순이익', '연결분기순이익(손실)'
                                          ]))
                }
            except Exception as ex:
                data_success = False
                continue

        if not data_success:
            today = datetime.now()
            end = today.strftime("%Y%m%d")
            start = (today - relativedelta(years=2)).strftime("%Y%m%d")
            url = 'https://opendart.fss.or.kr/api/list.json'
            params = {
                'crtfc_key': api_key,
                'corp_code': corp_code,
                'bgn_de':start,
                'end_de':end,
                'corp_cls':'E',
                'page_no':1,
                'page_count':10
            }
            result_json = {}

            for data in requests.get(url, params=params).json()['list']:
                date  = data['rcept_dt']
                rcept_no = data['rcept_no']

                url = 'https://opendart.fss.or.kr/api/document.xml'
                params = {
                    'crtfc_key': api_key,
                    'rcept_no': rcept_no
                }
                results = requests.get(url, params)
                with BytesIO(results.content) as zip_buffer:
                    with zipfile.ZipFile(zip_buffer, 'r') as zf:
                        xml_files = [name for name in zf.namelist() if name.endswith('.xml')]
                        if xml_files:
                            xml_file_name = xml_files[0]
                            xml_content = zf.read(xml_file_name).decode('utf-8')
                            result_json[date] = parse_financial_data_from_html_like_xml(xml_content)

        print(f'result_json : {result_json}')
        return result_json


def parse_financial_data_from_html_like_xml(xml_content: str) -> dict:

    parsed_data = {}
    try:
        root = ET.fromstring(xml_content)

        financial_items_map = {
            # 재무상태표
            '유동자산': {'keyword': '유동자산', 'acode_prefix': '11200000040000', 'table_title': '재 무 상 태 표'},
            '비유동자산': {'keyword': '비유동자산', 'acode_prefix': '11400000050000', 'table_title': '재 무 상 태 표'},
            '부채총계': {'keyword': '부채총계', 'acode_prefix': '11800000010000', 'table_title': '재 무 상 태 표'},
            '유동부채': {'keyword': '유동부채', 'acode_prefix': '11600000050000', 'table_title': '재 무 상 태 표'},
            '비유동부채': {'keyword': '비유동부채', 'acode_prefix': '11700000040000', 'table_title': '재 무 상 태 표'},
            '자산총계': {'keyword': '자산총계', 'acode_prefix': '11500000010000', 'table_title': '재 무 상 태 표'},
            '자본총계': {'keyword': '자본총계', 'acode_prefix': '11890000010000', 'table_title': '재 무 상 태 표'},
            '당좌자산': {'keyword': '당좌자산', 'acode_prefix': '11130000030000', 'table_title': '재 무 상 태 표'},  # 추가된 당좌자산

            # 손익계산서
            '매출액': {'keyword': '매출액', 'acode_prefix': '12100000010000', 'table_title': '손 익 계 산 서'},
            '매출총이익': {'keyword': '매출총이익', 'acode_prefix': '12300000010000', 'table_title': '손 익 계 산 서'},
            '영업이익': {'keyword': '영업이익', 'acode_prefix': '12500000010000', 'table_title': '손 익 계 산 서'},
            '당기순이익': {'keyword': '당기순이익', 'acode_prefix': '12900000010000', 'table_title': '손 익 계 산 서'},
        }

        for table_group in root.findall('.//TABLE-GROUP'):
            table_title_elem = table_group.find('./TITLE')
            current_table_title = table_title_elem.text.strip() if table_title_elem is not None and table_title_elem.text else ''

            for finance_table in table_group.findall('.//TABLE[@ACLASS="FINANCE"]'):

                for tr in finance_table.findall('TBODY/TR'):
                    text_element = tr.find('TE[@ADELIM="0"]')

                    if text_element is not None and text_element.text:
                        account_name_raw = text_element.text.strip().replace('\xa0', ' ').replace(' ', '')
                        acode = text_element.get('ACODE')

                        for item_key, item_info in financial_items_map.items():
                            if item_info['table_title'] not in current_table_title:
                                continue

                            if item_info['keyword'] in account_name_raw and acode and acode.startswith(
                                    item_info['acode_prefix']):
                                danggi_amount = None
                                jeongi_amount = None

                                amount_elem_danggi = tr.find('TE[@ADELIM="2"]')
                                if amount_elem_danggi is not None and amount_elem_danggi.text:
                                    clean_str_danggi = amount_elem_danggi.text.replace(',', '').strip()
                                    if re.fullmatch(r'^-?\d+$', clean_str_danggi) or re.fullmatch(r'^-?\d+\.\d+$',
                                                                                                  clean_str_danggi):
                                        danggi_amount = int(float(clean_str_danggi))

                                amount_elem_jeongi = tr.find('TE[@ADELIM="4"]')
                                if amount_elem_jeongi is not None and amount_elem_jeongi.text:
                                    clean_str_jeongi = amount_elem_jeongi.text.replace(',', '').strip()
                                    if re.fullmatch(r'^-?\d+$', clean_str_jeongi) or re.fullmatch(r'^-?\d+\.\d+$',
                                                                                                  clean_str_jeongi):
                                        jeongi_amount = int(float(clean_str_jeongi))

                                if danggi_amount is not None:
                                    parsed_data[item_key] = danggi_amount
                                else:
                                    if jeongi_amount is not None:
                                        parsed_data[item_key] = jeongi_amount
                                break

    except ET.ParseError as e:
        print(f"XML 파싱 오류: {e}")
        return {}
    except Exception as e:
        print(f"데이터 추출 중 오류 발생: {e}")
        return {}
    return parsed_data


if __name__ == "__main__":
    if not os.getenv("DART_KEY"):
        print("Warning: DART_KEY 환경 변수가 설정되지 않았습니다. 테스트를 위해 .env 파일을 확인하거나 직접 설정하세요.")

    financial_tool = CollectFinancialDataTool()
    test_company_name = input("테스트할 한국 기업 이름을 입력하세요 (예: 삼성전자): ")

    print(f"\nCollecting financial data for: {test_company_name}")
    try:
        financial_data_result = financial_tool._run(company_name=test_company_name)

        print("\n--- Financial Data Collection Result ---")
        import json
        print(json.dumps(financial_data_result, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"\nAn error occurred during tool execution: {e}")