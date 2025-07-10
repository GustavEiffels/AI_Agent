# app.py (or main.py)
import sys
import warnings
from datetime import datetime
import os
from typing import Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field # Pydantic BaseModel과 Field 임포트
from ai_test.crew import AiTest 
from dotenv import load_dotenv
import ai_test.tools.dart_tool as dart

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")


load_dotenv()

app = FastAPI(
    title="AI Financial Analysis Crew",
    description="API for running a CrewAI agent to perform financial analysis of Korean companies.",
    version="1.0.0",
)

# Pydantic 모델 정의: 요청 본문의 구조를 명시합니다.
class FinancialAnalysisRequest(BaseModel):
    topic: str = Field(..., example="삼성전자", description="The general topic for research (e.g., company name).")
    company_name: str = Field(..., example="삼성전자", description="The specific company name for financial analysis.")
    is_korean: bool = Field(..., example=True, description="True if the company is Korean, False otherwise.")

@app.post("/run") 
async def run_crew(request: FinancialAnalysisRequest) -> Dict: 
    company_name = request.company_name
    topic = request.topic
    is_korean_str = 'true' if request.is_korean else 'false' 

    if is_korean_str:
        result = dart.company_name_exist(request.company_name)
        print(f'result : {result}')
        if result['exist'] == False:
            return {"status": "fail", "company_name": company_name, "message": result['message']}



    inputs = {
        'topic': topic,
        'company_name': company_name,
        'is_korean': is_korean_str,
        'current_year': str(datetime.now().year) 
    }


    try:
        crew_instance = AiTest()
        
        result = crew_instance.crew().kickoff(inputs=inputs)
        
        return {"status": "success", "company_name": company_name, "analysis_report": result}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An error occurred while running the crew: {e}")

# Basic root endpoint
@app.get("/")
async def read_root():
    return {"message": "Welcome to the AI Financial Analysis Crew API!"}