import os, requests
import pandas as pd
from typing import Type, List
from dotenv import load_dotenv
import zipfile
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import OpenDartReader
from datetime import datetime
from io import BytesIO
from dateutil.relativedelta import relativedelta
import xml.etree.cElementTree as ET
import re
import json

load_dotenv()


# 🔹 Function to get financial quarters information
def get_financial_quarters_info(current_date=None):
    if current_date is None:
        current_date = datetime.now()

    current_year = current_date.year
    current_month = current_date.month
    current_day = current_date.day

    quarter_codes = {
        1: {'code': '11013', 'info_suffix': 'Q1', 'cutoff_month': 5, 'cutoff_day': 15},
        2: {'code': '11012', 'info_suffix': 'Q2', 'cutoff_month': 8, 'cutoff_day': 14},
        3: {'code': '11014', 'info_suffix': 'Q3', 'cutoff_month': 11, 'cutoff_day': 14},
        4: {'code': '11011', 'info_suffix': 'Q4', 'cutoff_month': 3, 'cutoff_day': 31}
    }

    financial_quarters = []

    latest_q_num_for_current_year = 0
    if (current_month > 5) or (current_month == 5 and current_day >= 15):
        latest_q_num_for_current_year = 1
    if (current_month > 8) or (current_month == 8 and current_day >= 14):
        latest_q_num_for_current_year = 2
    if (current_month > 11) or (current_month == 11 and current_day >= 14):
        latest_q_num_for_current_year = 3

    if current_month < quarter_codes[1]['cutoff_month'] or \
            (current_month == quarter_codes[1]['cutoff_month'] and current_day < quarter_codes[1]['cutoff_day']):
        latest_q_num_for_current_year = 4

    for q_num in range(1, latest_q_num_for_current_year + 1):
        year_to_use = current_year
        if q_num == 4 and latest_q_num_for_current_year == 4:
            year_to_use = current_year - 1

        financial_quarters.append({
            'year': year_to_use,
            'code': quarter_codes[q_num]['code'],
            'info': f"{year_to_use}년 {quarter_codes[q_num]['info_suffix']}",
            'q_num': q_num
        })

    years_to_cover = [current_year - 1, current_year - 2]

    for year in years_to_cover:
        for q_num in range(1, 5):
            quarter_info = quarter_codes[q_num]
            # --- 오류 수정 부분 ---
            if {'year': year, 'code': quarter_info['code'], 'q_num': q_num} not in [
                {'year': q_item['year'], 'code': q_item['code'], 'q_num': q_item['q_num']} for q_item in
                financial_quarters]:
                # --- 수정 끝 ---
                financial_quarters.append({
                    'year': year,
                    'code': quarter_info['code'],
                    'info': f"{year}년 {quarter_info['info_suffix']}",
                    'q_num': q_num
                })
    financial_quarters.sort(key=lambda x: (x['year'], x['q_num']), reverse=True)
    return {'all_quarters': financial_quarters}


# 🔹 Value extraction function (robust checks added, unchanged)
def convert(df: pd.DataFrame, mask: pd.Series):
    required_cols = ['sj_nm', 'account_nm', 'thstrm_amount']
    if not all(col in df.columns for col in required_cols):
        return None

    filtered_df = df.loc[mask]
    if filtered_df.empty:
        return None

    try:
        value = filtered_df.iloc[0]['thstrm_amount']
        if pd.isna(value):
            return None
        clean_value = str(value).replace(',', '').strip()
        if not clean_value or clean_value == '-':
            return None
        return int(float(clean_value))
    except (ValueError, TypeError) as e:
        return None
    except Exception as e:
        return None


# 🔹 Check company existence (no change)
def company_name_exist(name: str) -> dict:
    return_data = {
        'exist': True,
        'message': f'{name} Exist'
    }

    api_key = os.getenv("DART_KEY")
    if api_key is None:
        raise ValueError("DART_KEY environment variable is not set. Check your .env file.")

    dart = OpenDartReader(api_key)
    try:
        corp_info = dart.list(name)
    except Exception as e:
        return_data['exist'] = False
        return_data['message'] = f"Could not find company information for {name}: {e}"
        return return_data

    if corp_info is None or corp_info.empty:
        return_data['exist'] = False
        return_data['message'] = f"Could not find company information for {name}."
        return return_data

    filtered = corp_info[corp_info['corp_name'] == name]

    if filtered.empty:
        return_data['exist'] = False
        return_data['message'] = f"No company information found matching the exact name: {name}."

    return return_data


# 🔹 Pydantic input schema for CollectFinancialDataTool (no change)
class FinancialDataInput(BaseModel):
    company_name: str = Field(..., description="Exact name of the company to query (e.g., LG전자)")


# 🔹 Define the directory for temporary files
CURRENT_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT_DIR = os.path.join(CURRENT_FILE_DIR, '..', '..')
TEMP_XML_DIR = os.path.join(PROJECT_ROOT_DIR, 'temp_dart_xmls')


class CollectFinancialDataTool(BaseTool):
    name: str = "Collect Financial Data"
    description: str = (
        "Collects financial information (revenue, profit, assets, liabilities, etc.) for the latest 3 quarters from "
        "OpenDART API based on company name. If OpenDartReader fails to retrieve data, "
        "it downloads relevant original XML audit report files to a local directory and returns "
        "a list of their paths. If data is successfully collected, it returns the financial data in JSON format."
    )
    args_schema: Type[BaseModel] = FinancialDataInput

    def _run(self, company_name: str) -> dict:
        api_key = os.getenv("DART_KEY")
        if api_key is None:
            raise ValueError("DART_KEY environment variable is not set. Check your .env file.")

        dart = OpenDartReader(api_key)
        corp_info = dart.list(company_name)

        if corp_info is None or corp_info.empty:
            return {"status": "error", "message": f"Could not find company information for {company_name}."}

        filtered = corp_info[corp_info['corp_name'] == company_name]
        if filtered.empty:
            return {"status": "error",
                    "message": f"No company information found matching the exact name: {company_name}."}

        corp_code = filtered.iloc[0]['corp_code']
        print(f'Corp Code: {corp_code}')

        quarters_to_fetch = get_financial_quarters_info()['all_quarters']
        result_json_from_opendart = {}
        successful_opendart_fetches = 0

        for data in quarters_to_fetch:
            code = data['code']
            year = data['year']
            q_num = data['q_num']

            try:
                df1 = pd.DataFrame(dart.finstate_all(company_name, year, reprt_code=code, fs_div='CFS'))

                if df1.empty or not all(col in df1.columns for col in ['sj_nm', 'account_nm', 'thstrm_amount']):
                    print(
                        f"OpenDartReader returned empty or invalid DataFrame (missing key columns) for {year} Q{q_num}. Skipping to next quarter.")
                    continue

                quarter_data = {
                    'asset_moveable': convert(df1, (df1.sj_nm == '재무상태표') & (df1.account_nm == '유동자산')),
                    'asset_unmoveable': convert(df1, (df1.sj_nm == '재무상태표') & (df1.account_nm == '비유동자산')),
                    'bet_moveable': convert(df1, (df1.sj_nm == '재무상태표') & (df1.account_nm == '유동부채')),
                    'bet_unmoveable': convert(df1, (df1.sj_nm == '재무상태표') & (df1.account_nm == '비유동부채')),
                    'amount_bet': convert(df1, (df1.sj_nm == '재무상태표') & (df1.account_nm == '부채총계')),
                    'amount_asset': convert(df1, (df1.sj_nm == '재무상태표') & (
                        df1.account_nm.isin([
                            '자본총계', '반기말자본', '3분기말자본', '분기말자본', '1분기말자본']))),  # This actually targets Total Equity
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

                if any(v is not None for v in quarter_data.values()):
                    result_json_from_opendart[f'{year}_{q_num}Q'] = quarter_data
                    successful_opendart_fetches += 1
                else:
                    print(f"No meaningful data extracted for {year} Q{q_num} from OpenDartReader DataFrame.")

            except Exception as ex:
                print(f"Error processing {year} Q{q_num} data from OpenDartReader: {ex}")
                continue

        if successful_opendart_fetches > 0:
            print(f'Successfully collected {successful_opendart_fetches} quarters of data from OpenDartReader.')
            return {"status": "data_collected", "data": result_json_from_opendart}

        else:
            print(
                "Financial data collection via OpenDartReader failed or was completely empty. Falling back to downloading original XML files from DART disclosure list.")

            today = datetime.now()
            end = today.strftime("%Y%m%d")
            start = (today - relativedelta(years=4)).strftime("%Y%m%d")

            list_url = 'https://opendart.fss.or.kr/api/list.json'

            params = {
                'crtfc_key': api_key,
                'corp_code': corp_code,
                'bgn_de': start,
                'end_de': end,
                'corp_cls': 'E',  # Your original 'E' parameter
                'page_no': 1,
                'page_count': 10  # Your original page_count
            }

            downloaded_file_paths = []

            try:
                api_list_response = requests.get(list_url, params=params).json()
            except requests.exceptions.RequestException as e:
                print(f"Error making DART list API request during fallback: {e}")
                return {"status": "error", "message": f"DART list API request failed during fallback: {e}"}

            if 'list' not in api_list_response or not api_list_response['list']:
                print(
                    f"DART disclosure list API response (fallback) does not contain 'list' key or is empty: {api_list_response}")
                return {"status": "no_fallback_file", "message": "Could not retrieve disclosure list for fallback."}

            os.makedirs(TEMP_XML_DIR, exist_ok=True)

            for data in api_list_response['list']:
                # '감사보고서'이면서 '정정'이 아닌 보고서만 선택
                if '감사보고서' in data.get('report_nm', '') and '정정' not in data.get('report_nm', ''):
                    rcept_no = data['rcept_no']
                    doc_url = 'https://opendart.fss.or.kr/api/document.xml'
                    doc_params = {
                        'crtfc_key': api_key,
                        'rcept_no': rcept_no
                    }

                    try:
                        doc_results = requests.get(doc_url, params=doc_params)
                        doc_results.raise_for_status()
                    except requests.exceptions.RequestException as e:
                        print(f"Error downloading document (Receipt No: {rcept_no}) during fallback: {e}")
                        continue

                    if doc_results.status_code == 200:
                        with BytesIO(doc_results.content) as zip_buffer:
                            try:
                                with zipfile.ZipFile(zip_buffer, 'r') as zf:
                                    xml_files = [name for name in zf.namelist() if name.endswith('.xml')]
                                    if xml_files:
                                        xml_file_name = xml_files[0]

                                        unique_file_name = f"{rcept_no}_{xml_file_name}"
                                        save_path = os.path.join(TEMP_XML_DIR, unique_file_name)

                                        xml_content = zf.read(xml_file_name).decode('utf-8')
                                        with open(save_path, 'w', encoding='utf-8') as f:
                                            f.write(xml_content)
                                        print(
                                            f"Original XML file saved during fallback: {os.path.abspath(save_path)} (Report Name: {data.get('report_nm', 'N/A')})")
                                        downloaded_file_paths.append(os.path.abspath(save_path))
                                    else:
                                        print(
                                            f"ZIP file for {rcept_no} (Fallback) does not contain an XML file. Report Name: {data.get('report_nm', 'N/A')}")
                            except zipfile.BadZipFile:
                                print(
                                    f"Downloaded file for {rcept_no} (Fallback) is not a valid ZIP file. Report Name: {data.get('report_nm', 'N/A')}")
                                continue
                    else:
                        print(
                            f"Failed to download original document (Receipt No: {rcept_no}) during fallback, Status Code: {doc_results.status_code}. Report Name: {data.get('report_nm', 'N/A')}")

            if downloaded_file_paths:
                return {"status": "files_downloaded_needs_parsing", "file_paths": downloaded_file_paths}
            else:
                return {"status": "no_fallback_file",
                        "message": "OpenDartReader failed, and no XML files could be found or downloaded for fallback."}


# 🔹 ReadAndDeleteXmlFileInput Pydantic input schema (no change)
class ReadAndDeleteXmlFileInput(BaseModel):
    file_path: str = Field(..., description="Full path to the XML file stored locally.")


# 🔹 Custom Tool Definition: XML File Reading and Deletion Tool (no change)
class ReadAndDeleteXmlFileTool(BaseTool):
    name: str = "Read and Delete XML File"
    description: str = (
        "Reads the content of a locally stored XML file as a string and immediately deletes "
        "the file after reading. This tool does not parse the XML content; parsing is the "
        "responsibility of an agent's LLM capabilities."
    )
    args_schema: Type[BaseModel] = ReadAndDeleteXmlFileInput

    def _run(self, file_path: str) -> dict:
        print(f"ReadAndDeleteXmlFileTool: Starting to read file: {file_path}")
        if not os.path.exists(file_path):
            print(f"ReadAndDeleteXmlFileTool: Error - File not found: {file_path}")
            raise FileNotFoundError(f"Specified file not found: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()

            os.remove(file_path)
            print(f"ReadAndDeleteXmlFileTool: File read and deleted successfully: {file_path}")

            return {"status": "file_read_and_cleaned", "xml_content": xml_content}

        except Exception as e:
            print(f"ReadAndDeleteXmlFileTool: Error during XML file read/delete operation: {e}")
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"ReadAndDeleteXmlFileTool: Attempted to delete file due to error: {file_path}")
            raise RuntimeError(f"Error during XML file read or delete: {e}")


if __name__ == "__main__":
    # This block is for testing purposes and simulates agent tool calls in a CrewAI environment.
    if not os.getenv("DART_KEY"):
        print("Warning: DART_KEY environment variable is not set. Check your .env file or set it manually for testing.")

    api_key = os.getenv("DART_KEY")
    if api_key is None:
        print("DART_KEY is not set, skipping test.")
    else:
        # Create TEMP_XML_DIR if it doesn't exist
        os.makedirs(TEMP_XML_DIR, exist_ok=True)
        print(f"Temporary XML file storage directory: {TEMP_XML_DIR}")

        financial_tool = CollectFinancialDataTool()
        test_company_name = input("Enter the Korean company name to test (e.g., 삼성전자): ")

        print(f"\nCollecting financial data for: {test_company_name}")
        try:
            collection_result = financial_tool._run(company_name=test_company_name)

            print("\n--- Financial Data Collection Result ---")
            print(json.dumps(collection_result, indent=2, ensure_ascii=False))

            if collection_result.get("status") == "files_downloaded_needs_parsing":
                files_to_parse = collection_result["file_paths"]

                parsed_data_from_files = {}

                for file_path in files_to_parse:
                    print(f"\nFile downloaded. Using Read and Delete XML File tool to get XML content: {file_path}")

                    file_reader_tool = ReadAndDeleteXmlFileTool()
                    read_result = file_reader_tool._run(file_path=file_path)

                    print("\n--- Raw XML Content from Tool ---")
                    print(f"Status: {read_result.get('status')}")
                    if 'xml_content' in read_result:
                        print(f"Raw XML Content (truncated): {read_result['xml_content'][:500]}...")

                    print("\n--- Agent's LLM Parsing Simulation ---")
                    # LLM Prompt adjusted to specifically request the user's desired keys
                    agent_prompt_for_llm = f"""
                    The following is the original content of an XML document. Analyze this content and extract the most recent financial values for the period mentioned in the report.
                    Return the data in JSON format, where the top-level key is the period (e.g., "YYYY_Q" or "YYYY_Annual").

                    Extract values for the following financial items. Values should contain only numbers, remove commas (,), and currency symbols ('원'). If an item is not explicitly found, set its value to `null`.

                    Required Financial Items (use these exact keys in the JSON output):
                    - asset_moveable (Current Assets)
                    - asset_unmoveable (Non-Current Assets)
                    - bet_moveable (Current Liabilities)
                    - bet_unmoveable (Non-Current Liabilities)
                    - amount_bet (Total Liabilities)
                    - amount_asset (Total Capital/Equity)
                    - revenue (Revenue)
                    - gross_profit (Gross Profit)
                    - operating_income (Operating Income)
                    - net_income (Net Income)

                    XML Content:
                    ---
                    {read_result.get('xml_content', 'No content')}
                    ---

                    The response must be a valid JSON object only.
                    Example: {{"2023_1": {{"asset_moveable": 123456789, "revenue": 98765432, ...}}}}
                    """

                    # Mock LLM response structured exactly as requested
                    mock_period_key = "2023_1"  # Hardcoded for simulation, LLM would infer from XML

                    mock_llm_extracted_data = {
                        "asset_moveable": 214442141000000,
                        "asset_unmoveable": 239649636000000,
                        "bet_moveable": 76057448000000,
                        "bet_unmoveable": 18234913000000,
                        "amount_bet": 94292361000000,
                        "amount_asset": 359799416000000,
                        "revenue": 63745371000000,
                        "gross_profit": 17738278000000,
                        "operating_income": 640178000000,
                        "net_income": 1574600000000
                    }

                    mock_llm_response_json = {
                        mock_period_key: mock_llm_extracted_data
                    }

                    parsed_data_from_files.update(mock_llm_response_json)

                    print(
                        f"Agent's LLM extracted data for {os.path.basename(file_path)} (Period: {mock_period_key}): {json.dumps(mock_llm_response_json, indent=2, ensure_ascii=False)}")

                print("\n--- All Files Parsed Data (Aggregated by Period) ---")
                print(json.dumps(parsed_data_from_files, indent=2, ensure_ascii=False))

            elif collection_result.get("status") == "data_collected":
                print("\nData was collected directly via OpenDartReader. No further parsing needed.")
                print(f"Collected Data: {json.dumps(collection_result.get('data', {}), indent=2, ensure_ascii=False)}")

        except Exception as e:
            print(f"\nAn error occurred during tool execution: {e}")