import os, requests
import pandas as pd
from typing import Type
import xml.etree.ElementTree as ET
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import OpenDartReader
from datetime import datetime
from io import BytesIO
from dateutil.relativedelta import relativedelta
import base64

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


class XMLAnalyzerInput(BaseModel):
    # Base64 인코딩된 XML 문자열과 해당 공시가 어떤 기간의 것인지 힌트
    base64_xml_content: str = Field(..., description="Base64로 인코딩된 재무 보고서 XML 콘텐츠")
    report_date: str = Field(..., description="원본 보고서의 접수일 (YYYYMMDD 형식)")
    company_name: str = Field(..., description="보고서에 해당하는 회사 이름")

class XMLFinancialAnalyzerTool(BaseTool):
    name: str = "XML Financial Analyzer"
    description: str = (
        "Base64로 인코딩된 DART XML 재무 보고서를 디코딩하고 파싱하여 "
        "주요 재무 지표(매출, 이익, 자산, 부채 등)를 추출하고 구조화된 JSON 데이터로 반환합니다. "
        "재무 데이터 컬렉터 도구의 폴백 시 활용됩니다."
    )
    args_schema: Type[BaseModel] = XMLAnalyzerInput

    def _run(self, base64_xml_content: str, report_date: str, company_name: str) -> dict:
        try:
            # 1. Base64 디코딩
            decoded_xml_bytes = base64.b64decode(base64_xml_content.encode('utf-8'))
            print(f"Base64 디코딩 성공. XML 길이: {len(decoded_xml_bytes)} 바이트")

            # 2. dart-fss를 사용한 XBRL 파싱 시도 (권장)
            # dart-fss는 파일 경로를 받으므로 임시 파일로 저장
            temp_xml_path = f"temp_{report_date}_{company_name}.xml"
            try:
                with open(temp_xml_path, 'wb') as f:
                    f.write(decoded_xml_bytes)

                import dart_fss as dfs
                from dart_fss.errors import NotFoundConsolidated, NoDataReceived

                xbrl_obj = dfs.xbrl.DartXbrl(filename=temp_xml_path)
                financial_statements = None
                try:
                    financial_statements = xbrl_obj.get_financial_statement(fs_div='CFS', lang='ko',
                                                                            show_abstract=False)
                except NotFoundConsolidated:
                    financial_statements = xbrl_obj.get_financial_statement(fs_div='OFS', lang='ko',
                                                                            show_abstract=False)
                except NoDataReceived:
                    print(f"dart-fss: 재무제표를 찾을 수 없습니다 for {report_date}.")
                    financial_statements = pd.DataFrame()

                if financial_statements is not None and not financial_statements.empty:
                    # 'sj_nm' 컬럼 추가 및 컬럼명 통일 로직 (CollectFinancialDataTool의 _parse_xbrl_xml 참고)
                    def map_sj_div_to_sj_nm(row):
                        if 'BS' in row.get('sj_div', '') or 'BS' in row.get('fs_div', ''): return '재무상태표'
                        if 'IS' in row.get('sj_div', '') or 'IS' in row.get('fs_div', ''): return '손익계산서'
                        if 'CI' in row.get('sj_div', '') or 'CI' in row.get('fs_div', ''): return '포괄손익계산서'
                        if 'CF' in row.get('sj_div', '') or 'CF' in row.get('fs_div', ''): return '현금흐름표'
                        return None

                    financial_statements['sj_nm'] = financial_statements.apply(map_sj_div_to_sj_nm, axis=1)
                    df_parsed = financial_statements.rename(columns={
                        'value': 'thstrm_amount',
                        'concept_nm': 'account_nm',
                        'label_ko': 'account_nm'
                    })
                    required_cols = ['sj_nm', 'account_nm', 'thstrm_amount']
                    df_final = df_parsed[df_parsed['sj_nm'].notna()][required_cols]

                    # 여기서 DataFrame에서 필요한 재무 지표를 추출하여 딕셔너리 형태로 반환
                    # CollectFinancialDataTool의 _run 메서드에서 convert를 사용한 부분과 유사
                    parsed_financial_data = {
                        'asset_moveable': convert(df_final,
                                                  (df_final.sj_nm == '재무상태표') & (df_final.account_nm == '유동자산')),
                        'asset_unmoveable': convert(df_final,
                                                    (df_final.sj_nm == '재무상태표') & (df_final.account_nm == '비유동자산')),
                        'bet_moveable': convert(df_final,
                                                (df_final.sj_nm == '재무상태표') & (df_final.account_nm == '유동부채')),
                        'bet_unmoveable': convert(df_final,
                                                  (df_final.sj_nm == '재무상태표') & (df_final.account_nm == '비유동부채')),
                        'amount_bet': convert(df_final, (df_final.sj_nm == '재무상태표') & (df_final.account_nm == '부채총계')),
                        'amount_asset': convert(df_final, (df_final.sj_nm == '재무상태표') & (
                            df_final.account_nm.isin([
                                '자본총계', '반기말자본', '3분기말자본', '분기말자본', '1분기말자본']))),
                        'revenue': convert(df_final, (df_final.sj_nm.isin(['손익계산서', '포괄손익계산서'])) &
                                           df_final.account_nm.isin(['매출액', '수익(매출액)'])),
                        'gross_profit': convert(df_final, (df_final.sj_nm.isin(['손익계산서', '포괄손익계산서'])) &
                                                (df_final.account_nm == '매출총이익')),
                        'operating_income': convert(df_final, (df_final.sj_nm.isin(['손익계산서', '포괄손익계산서'])) &
                                                    df_final.account_nm.isin(['영업이익(손실)', '영업이익'])),
                        'net_income': convert(df_final, (df_final.sj_nm.isin(['손익계산서', '포괄손익계산서'])) &
                                              df_final.account_nm.isin([
                                                  '당기순이익(손실)', '당기순이익', '분기순이익', '분기순이익(손실)',
                                                  '반기순이익', '반기순이익(손실)', '연결분기순이익', '연결반기순이익',
                                                  '연결당기순이익', '연결분기(당기)순이익', '연결반기(당기)순이익', '연결분기순이익(손실)'
                                              ]))
                    }
                    print("XML Financial Analyzer: dart-fss로 데이터 추출 성공.")
                    return {"status": "success", "data": parsed_financial_data, "report_date": report_date}

            except Exception as e:  # dart-fss 로드 또는 사용 중 오류
                print(f"XML Financial Analyzer: dart-fss 파싱 오류: {e}. 일반 XML 파싱 시도.")
                try:
                    root = ET.fromstring(decoded_xml_bytes)
                 
                    found_value = None
                    for elem in root.iter():
                        if elem.tag == 'TE' and elem.text and '유동부채' in elem.text:
                            next_elem = elem.find('./following-sibling::TE[@ADELIM="2"]')  # 가정: ADELIM="2"에 값이 있음
                            if next_elem is not None and next_elem.text:
                                clean_val = next_elem.text.replace(',', '').strip()
                                if clean_val.isdigit():
                                    found_value = int(clean_val)
                                    break

                    if found_value is not None:
                        print(f"XML Financial Analyzer: ElementTree로 유동부채 {found_value} 추출 성공.")
                        return {"status": "success", "data": {"bet_moveable": found_value}, "report_date": report_date}
                    else:
                        print("XML Financial Analyzer: ElementTree로 데이터 추출 실패.")
                        return {"status": "error", "message": f"XML에서 재무 데이터를 파싱할 수 없습니다. (report_date: {report_date})"}

                except Exception as e_et:
                    print(f"XML Financial Analyzer: ElementTree 파싱 오류: {e_et}")
                    return {"status": "error", "message": f"XML 디코딩 및 파싱 오류: {e_et} (report_date: {report_date})"}
            finally:
                if os.path.exists(temp_xml_path):
                    os.remove(temp_xml_path)  # 임시 파일 삭제

        except Exception as e:
            return {"status": "error", "message": f"Base64 디코딩 오류: {e} (report_date: {report_date})"}
