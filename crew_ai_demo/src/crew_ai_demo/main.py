import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import re
import warnings
from datetime import datetime
import yfinance as yf
from .crew import CrewAiDemo
from .schemas import FullAnalysisReport

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


app = FastAPI()

class CrewInput(BaseModel):
    topic: str
    current_year: str = str(datetime.now().year)
    company_name: str

class CrewOutput(BaseModel):
    status: str
    original_report: str
    translated_report: str
    final_json_report: FullAnalysisReport # <-- FullAnalysisReport로 타입 유지 (이전 수정)
    action_command: str
    message: str

def execute_command(command: str):
    print(f"--- COMMAND EXECUTED: {command} ---")
    if command == "send_alert_to_admin":
        return "Admin alert sent successfully."
    elif command == "initiate_data_backup":
        return "Data backup initiated."
    else:
        return f"Unknown command: {command}. No action taken."


@app.get("/test")
def yahoooTest():
    test = yf.Ticker('TSLA')

    news = test.news
    if news:
        for i, item in enumerate(news[:3]):  # 최신 뉴스 3개
            print(f"\n뉴스 {i + 1}:")
            print(f"  제목: {item.get('title', 'N/A')}")
            print(f"  발행처: {item.get('publisher', 'N/A')}")
            print(f"  날짜: {item.get('providerPublishTime', 'N/A')}")
            print(f"  링크: {item.get('link', 'N/A')}")
            if item.get('summary'):
                print(f"  요약: {item.get('summary', 'N/A')[:200]}...")  # 요약이 길면 자름
    else:
        print("뉴스를 가져올 수 없습니다.")


@app.post("/run_analysis", response_model=CrewOutput)
async def run_crew_analysis(input_data: CrewInput):
    try:
        crew_instance = CrewAiDemo()
        my_crew = crew_instance.crew()

        print(f"CrewAI 실행 시작 - Topic: {input_data.topic}, Company: {input_data.company_name}, Year: {input_data.current_year}")

        crew_result = my_crew.kickoff(inputs={
            'topic': input_data.topic,
            'current_year': input_data.current_year,
            'company_name': input_data.company_name
        })


        print(f'input_data.current_year : {input_data.current_year}')

        final_json_string = ""
        if hasattr(crew_result, 'raw') and isinstance(crew_result.raw, str):
            final_json_string = crew_result.raw
        elif hasattr(crew_result, 'tasks_outputs') and crew_result.tasks_outputs:
            last_task_output = crew_result.tasks_outputs[-1]
            if hasattr(last_task_output, 'output') and isinstance(last_task_output.output, str):
                 final_json_string = last_task_output.output
            elif isinstance(last_task_output, str):
                final_json_string = last_task_output
            else:
                 print(f"경고: CrewOutput.tasks_outputs[-1]의 예상치 못한 타입: {type(last_task_output)}. 내용: {last_task_output}")

        if not final_json_string or final_json_string.strip() == "":
            print(f"경고: CrewAI 결과에서 유효한 JSON 문자열을 찾을 수 없습니다. CrewAI 결과 객체: {crew_result}")
            final_json_string = json.dumps({"error": "No valid JSON output found from CrewAI. Check agent/task output."})


        print(f"\n--- Raw JSON output from CrewAI for parsing: ---\n{final_json_string}\n--- End of Raw JSON ---\n")

        try:
            parsed_json_report = FullAnalysisReport.model_validate_json(final_json_string)
        except Exception as e:
            print(f"JSON 파싱 또는 유효성 검사 오류: {e}. Raw JSON: {final_json_string[:500]}...")
            # Fallback to an error object for the JSON report
            parsed_json_report = FullAnalysisReport(
                executive_summary="Error parsing JSON report or incomplete output from AI. Please check logs.",
                introduction={"title": "Parsing Error", "content": "Failed to parse introduction content."},
                company_overview={"title": "Parsing Error", "content": "Failed to parse company overview content."},
                products_and_technology_analysis={"title": "Parsing Error",
                                                  "content": "Failed to parse products and technology content."},
                market_status_and_competition={"title": "Parsing Error",
                                               "content": "Failed to parse market status content."},
                financial_analysis={
                    "key_financial_metrics": {
                        "Q_Error": {"current_assets_USD": 0, "non_current_assets_USD": 0, "current_liabilities_USD": 0,
                                    "non_current_liabilities_USD": 0, "operating_profit_USD": 0, "net_income_USD": 0,
                                    "current_ratio": 0, "debt_to_equity_ratio": 0, "quick_ratio_estimated": 0}},
                    "changes": {"QoQ_percent_changes": {}, "YoY_percent_changes": {}},
                    "financial_insights": ["Failed to parse financial insights."]
                },
                key_risk_factors={"title": "Parsing Error", "content": "Failed to parse key risk factors content."},
                recent_news=[],
                conclusion_and_recommendations={"title": "Parsing Error",
                                                "content": "Failed to parse conclusion and recommendations content."},
                sources=[],
                report_status="Parsing Error",
                action_command="None"
            )

        original_report_content = ""
        report_file_path = "report.md"
        if os.path.exists(report_file_path):
            with open(report_file_path, "r", encoding="utf-8") as f:
                original_report_content = f.read()
        else:
            print(f"경고: 원본 보고서 파일 '{report_file_path}'를 찾을 수 없습니다.")

        translated_report_content = ""
        translated_report_file_path = "report_korean.md"
        if os.path.exists(translated_report_file_path):
            with open(translated_report_file_path, "r", encoding="utf-8") as f:
                translated_report_content = f.read()
        else:
            print(f"경고: 번역된 보고서 파일 '{translated_report_file_path}'를 찾을 수 없습니다.")

        action_command_match = re.search(r"ACTION_COMMAND: (.*)", original_report_content)
        action_command = action_command_match.group(1).strip() if action_command_match else "None"

        command_execution_result = "No command to execute."
        if action_command and action_command != "None":
            command_execution_result = execute_command(action_command)

        return CrewOutput(
            status="success",
            original_report=original_report_content,
            translated_report=translated_report_content,
            final_json_report=parsed_json_report,
            action_command=action_command,
            message=f"CrewAI analysis complete. Command executed: {command_execution_result}"
        )

    except Exception as e:
        print(f"Error running CrewAI: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))