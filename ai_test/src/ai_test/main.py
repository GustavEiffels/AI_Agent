import time
import functools
import json
import warnings
from contextlib import asynccontextmanager
from typing import Any, Callable
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from .crew import AiTest
from dotenv import load_dotenv
from .tools.dart_tool import company_name_exist as dart
from .nosql import connect_to_mongodb, close_mongo_connection, save_data_to_collections, get_data_by_criteria
from datetime import datetime, time
import time as time_module

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

@app.post("/run")
@time_it
async def run_crew(request: FinancialAnalysisRequest) -> dict[str, str | Any] | str:

    company_name = request.company_name
    topic = request.topic
    is_korean_str = request.is_korean

    print(f'is_korean_str : {is_korean_str}')


    if is_korean_str:
        result = dart(request.company_name)
        print(f'result : {result}')
        if not result['exist']:
            return {"status": "fail", "company_name": company_name, "message": result['message']}

    now = datetime.now()
    current_month_year = now.strftime("%Y-%m")

    finance_info = await get_data_by_criteria(
        collection_name='finance_collection',
        company_name=company_name,
        category='finance',
        current_month=current_month_year
    )

    if finance_info is not None:
        return {"status": "success", "company_name": company_name, "analysis_result": finance_info}


    inputs = {
        'topic': topic,
        'company_name': company_name,
        'is_korean': is_korean_str,
        'current_year': str(datetime.now().year) 
    }

    try:
        crew_instance = AiTest()
        result = crew_instance.crew().kickoff(inputs=inputs)
        final_json_output = json.loads(result.raw)

        finance_insert_info = {
            'collection_name':'finance_collection',
            'company_name':f'{company_name}',
            'category':'finance',
            'current_month':f'{current_month_year}',
            'finance_info':final_json_output
        }

        print(f'store data : {finance_insert_info}')

        await save_data_to_collections(finance_insert_info)


        return {"status": "success", "company_name": company_name, "analysis_result": final_json_output}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An error occurred while running the crew: {e}")

# Basic root endpoint
@app.get("/")
@time_it
async def read_root():
    return {"message": "Welcome to the AI Financial Analysis Crew API!"}