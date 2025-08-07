import functools, os
import json
import warnings
import traceback
from contextlib import asynccontextmanager
from typing import Any, Callable
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel, Field
from .crew import AiTest
from dotenv import load_dotenv
from .tools.dart_tool import company_name_exist as dart
from .nosql import connect_to_mongodb, close_mongo_connection, save_data_to_collections, get_data_by_criteria
from datetime import datetime
from ai_test.hs_crew import SalesforceCrewai
from ai_test.gs_crew import AbmAi
import time as time_module
import asyncio
import requests
from uuid import uuid4
from typing import Dict, List
from ai_test.jh_crew import SbtProject
import ai_test.simple_main_sfdc as sfdc_connect

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("FastAPI lifespan: Connecting to MongoDB...")
    await connect_to_mongodb()
    try:
        yield
    finally:
        await close_mongo_connection()

app = FastAPI(
    title="AI Financial Analysis Crew",
    description="API for running a CrewAI agent to perform financial analysis of Korean companies.",
    version="1.0.0",
    lifespan=lifespan
)
RESULT_DIR = "results"

def time_it(func: Callable) -> Callable:
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time_module.time()
        result = await func(*args, **kwargs)
        end_time = time_module.time()
        process_time = end_time - start_time
        print(f"Function '{func.__name__}' executed in {process_time:.4f} seconds")
        if isinstance(result, dict):
            new_result = result.copy()
            new_result["process_time_seconds"] = f"{process_time:.4f}"
            return new_result
        elif isinstance(result, str):
            return {"message": result, "process_time_seconds": f"{process_time:.4f}"}
        else:
            return result

    return wrapper

# Pydantic 모델 정의: 요청 본문의 구조를 명시합니다.
class FinancialAnalysisRequest(BaseModel):
    topic: str = Field(..., example="삼성전자", description="The general topic for research (e.g., company name).")
    company_name: str = Field(..., example="삼성전자", description="The specific company name for financial analysis.")
    is_korean: bool = Field(..., example=True, description="True if the company is Korean, False otherwise.")

class StandardResponse(BaseModel):
    code: int = Field(..., description="HTTP status-like code (e.g., 200 for success, 500 for error)")
    message: str = Field(..., description="A human-readable message about the operation status")
    company_name: str = Field(..., description="SBT GLOBAL")
    category: str = Field(..., description="Categorization of the response (e.g., 'finance_analysis', 'sales_activity', 'error')")
    data: Any = Field(None, description="The actual data payload, can be any JSON-serializable object")

async def run_finance_analysis_crew_in_background(inputs: Dict[str, Any]):
    """
    CrewAI 금융 분석 작업을 백그라운드에서 실행하고, 결과를 DB에 저장합니다.
    """
    company_name = inputs.get('company_name', 'Unknown Company')
    current_month_year = inputs.get('current_month_year', 'N/A')  # current_month_year 추가
    print(f"\n[Background Task] CrewAI 금융 분석 시작 (회사: {company_name}, 월: {current_month_year})")

    result_to_save = None
    try:
        crew_instance = AiTest()
        # CrewAI를 실행하고 결과를 받습니다. (동기 함수이므로 asyncio.to_thread 사용)
        crew_output_object = await asyncio.to_thread(crew_instance.crew().kickoff, inputs=inputs)

        # CrewOutput 객체의 .raw 속성이 최종 결과 문자열을 포함합니다.
        raw_summary_string_from_output = crew_output_object.raw

        # CrewAI 출력의 불필요한 외부 따옴표를 제거 (있을 경우)
        if isinstance(raw_summary_string_from_output, str) and \
                raw_summary_string_from_output.startswith("'") and raw_summary_string_from_output.endswith("'"):
            raw_summary_string_from_output = raw_summary_string_from_output[1:-1]

        # JSON 문자열을 파이썬 객체로 파싱합니다.
        final_json_output = None
        try:
            final_json_output = json.loads(raw_summary_string_from_output)
        except json.JSONDecodeError as json_err:
            print(f"[Background Task] JSON 파싱 에러: {json_err}")
            print(f"[Background Task] 파싱 시도 문자열: {raw_summary_string_from_output}")
            # 파싱 실패 시, 원시 문자열 자체를 결과로 사용하거나 오류 처리
            final_json_output = {"error": "JSON 파싱 실패", "raw_output_string": raw_summary_string_from_output}
        except Exception as e:
            print(f"[Background Task] 예상치 못한 파싱 오류: {e}")
            final_json_output = {"error": "알 수 없는 파싱 오류", "raw_output_string": raw_summary_string_from_output}

        # MongoDB에 분석 결과 저장
        finance_insert_info = {
            'collection_name': 'finance_collection',
            'company_name': company_name,
            'category': 'finance',
            'current_month': current_month_year,
            'finance_info': final_json_output  # 파싱된 JSON 객체를 저장
        }

        print(f'SAVE TO DB DATA : {finance_insert_info}')


        result_to_save = StandardResponse(
            code=200,
            message=f"{company_name} Finance analysis completed successfully.",
            category="Financial",
            company_name=f"{company_name}",
            data=final_json_output
        )
        print(f'SEND TO SFDC DATA : {result_to_save}')
        sfdc_connect.send_to_sfdc(result_to_save)

        print(
            f'[Background Task] 데이터베이스에 저장: {finance_insert_info.get("company_name")} - {finance_insert_info.get("current_month")}')
        await save_data_to_collections(finance_insert_info)
        print(f'[Background Task] CrewAI 금융 분석 완료 (회사: {company_name})')

    except Exception as e:
        print(f"\n[Background Task] CrewAI 금융 분석 중 심각한 오류 발생: {e}")
        traceback.print_exc()
        result_to_save = StandardResponse(
            code=500,
            message=f"{company_name} Finance analysis completed Fail.",
            category="Financial",
            companyName=f"{company_name}",
            data=e
        )
        sfdc_connect.send_to_sfdc(result_to_save)

# --- FastAPI Endpoint ---
@app.post("/finance_analysis")
@time_it  # @time_it 데코레이터가 정의되어 있어야 합니다.
async def finance_analysis(
        request: FinancialAnalysisRequest,  # 요청 본문에서 Pydantic 모델을 받음
        background_tasks: BackgroundTasks  # 백그라운드 태스크 의존성 주입
) -> dict[str, str | Any]:  # 반환 타입 명확화

    company_name = request.company_name
    topic = request.topic
    is_korean_str = request.is_korean

    print(f'API Call: /finance_analysis for {company_name} (Korean: {is_korean_str})')

    # 현재 월/년 정보 생성 (캐싱 및 DB 저장에 사용)
    now = datetime.now()
    current_month_year = now.strftime("%Y-%m")

    # DART API 호출 (회사 이름이 한글일 경우에만)
    if is_korean_str:
        dart_result = dart(company_name)
        if not dart_result['exist']:
            # DART에서 회사 정보가 없으면 즉시 실패 응답 반환
            return {"status": "fail", "company_name": company_name, "message": dart_result['message']}

    # MongoDB에서 기존 분석 정보 조회
    finance_info = await get_data_by_criteria(
        collection_name='finance_collection',
        company_name=company_name,
        category='finance',
        current_month=current_month_year
    )

    if finance_info is not None:
        # 기존 데이터가 있으면 즉시 반환 (캐싱 히트)
        print(f"캐싱된 분석 결과 발견 및 반환: {company_name} ({current_month_year})")
        return {"status": "success", "company_name": company_name, "analysis_result": finance_info}

    # CrewAI 실행을 위한 입력 데이터 준비
    inputs = {
        'topic': topic,
        'company_name': company_name,
        'is_korean': is_korean_str,
        'current_year': str(datetime.now().year),
        'current_month_year': current_month_year  # 백그라운드 함수에 전달
    }

    print(f"새로운 분석 요청: CrewAI 백그라운드 작업 시작 (회사: {company_name})")
    # CrewAI 작업을 백그라운드 태스크로 추가하고 즉시 응답 반환
    background_tasks.add_task(run_finance_analysis_crew_in_background, inputs)

    # 클라이언트에게 즉시 응답 반환 (작업이 백그라운드에서 시작되었음을 알림)
    return {
        "status": "processing",
        "company_name": company_name,
        "message": "재무 분석이 백그라운드에서 시작되었습니다. 잠시 후 데이터를 다시 조회해 주세요."
    }


# Basic root endpoint
@app.get("/")
@time_it
async def read_root():
    return {"message": "Welcome to the AI Financial Analysis Crew API! KAGOSHIMA 0923"}


# CrewAI 작업을 백그라운드에서 실행할 함수
async def run_salesforce_crew_in_background(inputs: dict):
    try:
        salesforce_crew = SalesforceCrewai()
        crew_output_object = await asyncio.to_thread(salesforce_crew.run, inputs=inputs)

        # 실제 CrewAI 결과 처리 (로그 또는 다른 저장 메커니즘 사용)
        print(f"Background CrewAI completed at {datetime.now()} >>")
        print(f'CrewOutput Object Type: {type(crew_output_object)}')

        # 최종 결과는 crew_output_object.raw 에 있을 가능성이 높습니다.
        raw_summary_string_from_output = crew_output_object.raw
        final_parsed_list = None

        if isinstance(raw_summary_string_from_output, str) and \
                raw_summary_string_from_output.startswith("'") and raw_summary_string_from_output.endswith("'"):
            raw_summary_string_from_output = raw_summary_string_from_output[1:-1]

        try:
            final_parsed_list = json.loads(raw_summary_string_from_output)
        except json.JSONDecodeError:
            final_parsed_list = raw_summary_string_from_output
            print("Warning: CrewOutput.raw was already a list/dict in background, no JSON parsing needed.")

        print(f'Final Parsed List (Background): {final_parsed_list}')

        result_to_save = StandardResponse(
            code=200,
            message="Salesforce Org's analysis completed successfully.",
            company_name='',
            category="Analysis",
            data=final_parsed_list
        )


    except Exception as e:
        print(f"Background CrewAI error at {datetime.now()}: {e}")
        result_to_save = StandardResponse(
            code=500,
            message=f"Salesforce Org's analysis Fail : {e}",
            company_name='',
            category="Analysis",
            data=e
        )
        traceback.print_exc()

    print(f'before send to sfdc : {result_to_save}')
    sfdc_connect.send_to_sfdc(result_to_save)


@app.get('/org_analysis')
async def hs_test(background_tasks: BackgroundTasks):
    print("inputs 실행 성공>>")
    current_year = str(datetime.now().year)
    inputs = {'current_year': current_year}

    print("inputs 실행 성공:", inputs)

    # CrewAI 작업을 백그라운드 태스크로 추가
    background_tasks.add_task(run_salesforce_crew_in_background, inputs)

    # 즉시 응답 반환
    return {
        'message': 'CrewAI is running in the background. Please check logs for completion or query a status endpoint later.'}


# GS
class ABMRequest(BaseModel):
    AccountName: str
    AnnualRevenue: str
    Industry: str

def search_serper(query: str) -> str:
    api_key = os.getenv("GS_SERPER_API_KEY")
    if not api_key:
        raise ValueError("GS_SERPER_API_KEY not set")

    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    payload = {"q": query}
    response = requests.post(url, json=payload, headers=headers)
    json_data = response.json()
    organic = json_data.get("organic", [])
    return "\n".join([
        f"- {item.get('title')} ({item.get('link')})" for item in organic
    ]) or "검색 결과 없음"

@app.post("/email_template")
async def run_abm(request: ABMRequest, background_tasks: BackgroundTasks):
    search_data = search_serper(request.AccountName)
    job_id = str(uuid4())

    print('job_id : '+job_id)

    inputs = {
        "AccountName": request.AccountName,
        "AnnualRevenue": request.AnnualRevenue,
        "Industry": request.Industry,
        "Search_Data": search_data,
    }

    background_tasks.add_task(run_abm_job, inputs, job_id)

    return {"job_id": job_id, "status": "accepted"}

def run_abm_job(inputs: dict, job_id: str):
    try:
        result = AbmAi().crew().kickoff(inputs=inputs)

        os.makedirs("results", exist_ok=True)

        with open(f"results/{job_id}.json", "w", encoding="utf-8") as f:
            json.dump({"output": str(result)}, f, ensure_ascii=False)
    except Exception as e:
        with open(f"results/{job_id}.json", "w", encoding="utf-8") as f:
            json.dump({"error": str(e)}, f)


## JH

class Activity(BaseModel):
    ActivityDate: str = Field(..., example="2024-06-09", description="활동 발생 날짜 (YYYY-MM-DD)")
    Subject: str = Field(..., example="공고", description="활동의 주제 또는 제목")
    Description: str = Field(..., example="• 사업기간 : 2024년 10월 ~ 2025년 9월 (12개월)...", description="활동에 대한 상세 설명")


class SalesActivity(BaseModel):
    company: str = Field(..., example="현대자동차", description="분석 대상 회사의 이름")
    activity: List[Activity] = Field(..., description="회사와 관련된 영업 활동 리스트")

async def run_crew_process_in_background(inputs: Dict):
    company_name = inputs.get('company', 'Unknown Company')
    print(f"백그라운드 CrewAI 프로세스 시작 (회사: {company_name})")

    result_to_save: StandardResponse # Type hint for clarity

    try:
        crew_instance = SbtProject()
        crew_output_object  = await asyncio.to_thread(crew_instance.crew().kickoff, inputs=inputs)
        raw_result_string = crew_output_object.raw
        print(f'CrewAI 프로세스 완료 - 원시 결과 문자열: {raw_result_string}')

        parsed_result = None
        try:
            parsed_result = json.loads(raw_result_string)
            print("CrewAI 결과가 성공적으로 JSON으로 파싱되었습니다.")
            result_to_save = StandardResponse( # <-- This is where StandardResponse is used
                code=200,
                message="Sales activity analysis completed successfully.",
                category="Summary",
                company_name=f"{company_name}",
                data=parsed_result
            )
        except json.JSONDecodeError as e:
            print(f"JSON 디코딩 오류 발생: {e}")
            print(f"원시 문자열에서 JSON 블록 추출 시도 중...")
            import re
            json_match = re.search(r'```json\n(.*?)```', raw_result_string, re.DOTALL)
            if json_match:
                json_string = json_match.group(1)
                try:
                    parsed_result = json.loads(json_string)
                    print("JSON 블록을 성공적으로 추출하고 파싱했습니다.")
                    result_to_save = StandardResponse( # <-- This is where StandardResponse is used
                        code=200,
                        message="Sales activity analysis completed (JSON extracted).",
                        category="Summary",
                        company_name=f"{company_name}",
                        data=parsed_result
                    )
                except json.JSONDecodeError as inner_e:
                    print(f"추출된 JSON 블록 파싱 오류: {inner_e}")
                    result_to_save = StandardResponse( # <-- This is where StandardResponse is used
                        code=500,
                        message=f"Sales activity analysis completed but JSON block parsing failed: {inner_e}",
                        category="Summary",
                        company_name=f"{company_name}",
                        data={"raw_output": raw_result_string} # Ensure this is JSON-serializable
                    )
            else:
                result_to_save = StandardResponse( # <-- This is where StandardResponse is used
                    code=500,
                    message="Sales activity analysis completed but no parsable JSON block found.",
                    category="Summary",
                    company_name=f"{company_name}",
                    data={"raw_output": raw_result_string}
                )

        print(f"최종 파싱된 CrewAI 결과 (회사: {company_name}): {result_to_save}")

        sfdc_connect.send_to_sfdc(result_to_save)


    except Exception as e:
        print(f"\n백그라운드 CrewAI 프로세스 실행 중 오류 발생 (회사: {company_name}): {e}")
        traceback.print_exc()
        error_result_to_save = StandardResponse(
            code=500,
            message=f"Critical error during sales activity analysis: {str(e)}",
            category="Summary",
            data={"traceback": traceback.format_exc()}
        )



# --- FastAPI 엔드포인트 ---

@app.post("/activity_summary")  # POST 엔드포인트로 변경
async def analyze_sales_activity(
        sales_data: SalesActivity,  # 요청 본문으로부터 SalesActivity 모델을 받음
        background_tasks: BackgroundTasks
):
    print('API 엔드포인트 호출됨: CrewAI 프로세스 시작 중...')

    inputs = sales_data.dict()  # Pydantic 모델을 딕셔너리로 변환
    raw_inputs = sales_data.dict()

    # CrewAI 태스크에서 'sales_activity' 변수를 기대하므로,
    # 'activity' 데이터를 'sales_activity' 키로 전달하도록 수정합니다.
    inputs = {
        "company": raw_inputs.get("company"),
        "sales_activity": raw_inputs.get("activity") # 'activity' 리스트를 'sales_activity' 키로 매핑
    }

    # CrewAI 작업을 백그라운드 태스크로 추가
    background_tasks.add_task(run_crew_process_in_background, inputs)

    # 즉시 응답 반환
    return {
        'message': f'CrewAI가 백그라운드에서 {sales_data.company}에 대한 영업 활동 분석을 시작합니다.',
        'status': 'processing'
    }