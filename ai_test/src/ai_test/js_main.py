from typing import Dict, List
from ai_test.jh_crew import SbtProject
from fastapi import FastAPI, BackgroundTasks, Body  # Body 임포트 추가
from pydantic import BaseModel, Field  # BaseModel, Field 임포트 추가
import asyncio
import json
import traceback
import warnings
from dotenv import load_dotenv

app = FastAPI()
load_dotenv()

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

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
    try:
        crew_instance = SbtProject()
        # kickoff 메서드는 최종 태스크의 raw 문자열 출력을 반환합니다.
        raw_result_string = await asyncio.to_thread(crew_instance.crew().kickoff, inputs=inputs)

        print(f'CrewAI 프로세스 완료 - 원시 결과 문자열: {raw_result_string}')  # 디버깅을 위한 원시 결과 출력

        parsed_result = None
        try:
            parsed_result = json.loads(raw_result_string)
            print("CrewAI 결과가 성공적으로 JSON으로 파싱되었습니다.")
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
                except json.JSONDecodeError as inner_e:
                    print(f"추출된 JSON 블록 파싱 오류: {inner_e}")
                    parsed_result = {"error": "JSON 파싱 실패 (추출 후)", "raw_output": raw_result_string}
            else:
                parsed_result = {"error": "JSON 파싱 실패 (JSON 블록 없음)", "raw_output": raw_result_string}

        # 최종 파싱된 결과 출력 (또는 DB/파일 저장)
        print(f"최종 파싱된 CrewAI 결과 (회사: {company_name}): {parsed_result}")
        # TODO: 여기에 parsed_result를 데이터베이스에 저장하거나,
        # 다른 API로 전송하거나, 파일로 저장하는 등의 후속 로직을 추가하세요.

    except Exception as e:
        print(f"\n백그라운드 CrewAI 프로세스 실행 중 오류 발생 (회사: {company_name}): {e}")
        traceback.print_exc()  # 오류 스택 트레이스 출력


# --- FastAPI 엔드포인트 ---

@app.post("/analyze_sales_activity")  # POST 엔드포인트로 변경
async def analyze_sales_activity(
        sales_data: SalesActivity,  # 요청 본문으로부터 SalesActivity 모델을 받음
        background_tasks: BackgroundTasks
):
    """
    영업 활동 데이터를 받아 백그라운드에서 CrewAI 분석 작업을 시작합니다.
    분석 작업은 즉시 반환되며, 결과는 백그라운드에서 처리됩니다.
    """
    print('API 엔드포인트 호출됨: CrewAI 프로세스 시작 중...')

    # Pydantic 모델에서 받은 데이터를 CrewAI 입력 형식에 맞게 변환 (이미 맞는 형식)
    inputs = sales_data.dict()  # Pydantic 모델을 딕셔너리로 변환

    print(f'CrewAI에 전달될 입력: {inputs.get("company", "N/A")}')

    # CrewAI 작업을 백그라운드 태스크로 추가
    background_tasks.add_task(run_crew_process_in_background, inputs)

    # 즉시 응답 반환
    return {
        'message': f'CrewAI가 백그라운드에서 {sales_data.company}에 대한 영업 활동 분석을 시작합니다.',
        'status': 'processing'
    }