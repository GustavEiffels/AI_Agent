from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import re
import warnings
from datetime import datetime

# CrewAiDemo 클래스의 실제 경로에 맞게 임포트 경로를 수정하세요.
# 예: your_project_root/src/crewai_demo/crew.py
from .crew import CrewAiDemo  # CrewAiDemo 대신 MyAnalysisCrew로 이름 변경 가정

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

if not os.getenv("OPENAI_API_KEY") and not os.getenv("GROQ_API_KEY"):
    print("경고: OPENAI_API_KEY 또는 GROQ_API_KEY가 설정되지 않았습니다.")
    print("환경 변수를 설정하거나 main.py 파일에 직접 입력하세요 (프로덕션 환경에서는 권장하지 않음).")

app = FastAPI()

class CrewInput(BaseModel):
    topic: str
    current_year: str = str(datetime.now().year)
    company_name: str # Add company_name as a required field

class CrewOutput(BaseModel):
    status: str
    original_report: str
    translated_report: str
    action_command: str
    message: str

# 특정 명령을 실행하는 가상의 함수
def execute_command(command: str):
    print(f"--- COMMAND EXECUTED: {command} ---")
    if command == "send_alert_to_admin":
        # 실제 알림 시스템 (Slack, Email 등) 호출 로직
        return "Admin alert sent successfully."
    elif command == "initiate_data_backup":
        # 실제 백업 스크립트 실행 또는 클라우드 백업 API 호출 로직
        return "Data backup initiated."
    else:
        return f"Unknown command: {command}. No action taken."


@app.post("/run_analysis", response_model=CrewOutput)
async def run_crew_analysis(input_data: CrewInput):
    try:
        crew_instance = CrewAiDemo ()
        my_crew = crew_instance.crew()

        print(f"CrewAI 실행 시작 - Topic: {input_data.topic}, Company: {input_data.company_name}, Year: {input_data.current_year}")

        crew_result = my_crew.kickoff(inputs={
            'topic': input_data.topic,
            'current_year': input_data.current_year,
            'company_name': input_data.company_name # ADD THIS LINE: Pass company_name to kickoff
        })

        if hasattr(crew_result, 'raw') and isinstance(getattr(crew_result, 'raw'), str):
            final_translated_report = crew_result.raw
        elif isinstance(crew_result, str):
            final_translated_report = crew_result
        else:
            # 예상치 못한 형식의 경우, 오류를 발생시키거나 빈 문자열 처리
            print(f"경고: 예상치 못한 CrewAI 결과 타입: {type(crew_result)}. 내용: {crew_result}")
            final_translated_report = "Error: Unexpected CrewAI output format."

        original_report_content = ""
        report_file_path = "report.md"
        if os.path.exists(report_file_path):
            with open(report_file_path, "r", encoding="utf-8") as f:
                original_report_content = f.read()
        else:
            print(f"경고: 원본 보고서 파일 '{report_file_path}'를 찾을 수 없습니다.")

        action_command_match = re.search(r"ACTION_COMMAND: (.*)", original_report_content)
        action_command = action_command_match.group(1).strip() if action_command_match else "None"

        command_execution_result = "No command to execute."
        if action_command and action_command != "None":
            command_execution_result = execute_command(action_command)

        return CrewOutput(
            status="success",
            original_report=original_report_content,
            translated_report=final_translated_report,
            action_command=action_command,
            message=f"CrewAI analysis complete. Command executed: {command_execution_result}"
        )

    except Exception as e:
        print(f"Error running CrewAI: {e}")
        raise HTTPException(status_code=500, detail=str(e))

