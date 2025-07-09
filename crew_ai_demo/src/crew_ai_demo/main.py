from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import re
import warnings
from datetime import datetime
import yfinance as yf
import json
from .schemas import FullAnalysisReport 

from .crew import CrewAiDemo  # CrewAiDemo 대신 MyAnalysisCrew로 이름 변경 가정
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

app = FastAPI()

class CrewInput(BaseModel):
    topic: str
    current_year: str = str(datetime.now().year)
    company_name: str # Add company_name as a required field
    current_date: str = datetime.now().strftime("%Y-%m-%d")

class CrewOutput(BaseModel):
    status: str
    original_report: str
    translated_report: str
    json_data: FullAnalysisReport
    action_command: str
    message: str

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

@app.get("/{ticker_symbol}")
def test_yahoo_news_simple(ticker_symbol: str):
    """
    야후 파이낸스에서 특정 기업의 최신 뉴스 3개를 조회하는 간단한 테스트 엔드포인트.
    기사 주소, 제목, 발행 날짜만 추출합니다.
    """
    if not ticker_symbol:
        raise HTTPException(status_code=400, detail="Ticker symbol is required.")

    print(f"Fetching Yahoo Finance news for ticker: {ticker_symbol}")
    print(f'ticker_symbol : {ticker_symbol}')

    extracted_news_data = [] # 추출된 뉴스 데이터를 담을 리스트

    try:
        ticker = yf.Ticker(ticker_symbol)
        all_news_items = ticker.news # yfinance에서 가져온 모든 뉴스 아이템 리스트
        
        if all_news_items:
            for i, item in enumerate(all_news_items[:3]):  # 최신 뉴스 3개만 처리
                # 모든 필요한 정보는 'content' 딕셔너리 안에 있습니다.
                content = item.get('content', {}) 

                title = content.get('title', 'N/A')
                # 'pubDate'는 'YYYY-MM-DDTHH:MM:SSZ' 형식이므로, 날짜 부분만 추출
                pub_date_raw = content.get('pubDate')
                publish_date = "N/A"
                if pub_date_raw:
                    try:
                        # ISO 8601 문자열을 datetime 객체로 파싱 후 'YYYY-MM-DD'로 포맷
                        publish_date = datetime.fromisoformat(pub_date_raw.replace('Z', '+00:00')).strftime('%Y-%m-%d')
                    except ValueError:
                        publish_date = "Invalid Date Format"
                
                # URL은 'canonicalUrl' 또는 'clickThroughUrl' 안의 'url' 필드에 있을 수 있습니다.
                # 우선 'canonicalUrl'을 시도하고, 없으면 'clickThroughUrl'을 시도합니다.
                url = content.get('canonicalUrl', {}).get('url', 'N/A')
                if url == 'N/A': # canonicalUrl이 없으면 clickThroughUrl을 시도
                    url = content.get('clickThroughUrl', {}).get('url', 'N/A')

                news_entry = {
                    "title": title,
                    "published_date": publish_date,
                    "url": url
                }
                extracted_news_data.append(news_entry)

                # 콘솔 출력 (디버깅용)
                print(f"\n--- Extracted News {i + 1} ---")
                print(f"  제목: {news_entry['title']}")
                print(f"  발행 날짜: {news_entry['published_date']}")
                print(f"  링크: {news_entry['url']}")

        else:
            print(f"야후 파이낸스에서 {ticker_symbol} 뉴스를 가져올 수 없습니다.")
            # 뉴스가 없는 경우에도 일관된 응답 구조를 위해 메시지 포함
            extracted_news_data.append({"message": f"No news found for {ticker_symbol}."})

    except Exception as e:
        print(f"야후 파이낸스 뉴스 가져오기 중 오류 발생: {e}")
        import traceback
        traceback.print_exc() # 오류 스택 트레이스 출력
        raise HTTPException(status_code=500, detail=f"Failed to fetch news: {e}")
    
    # JSON 응답으로 반환
    return {
        "ticker": ticker_symbol,
        "extracted_news": extracted_news_data, # 변경된 필드명
        "message": "News extraction attempt complete."
    }



# --- 메인 CrewAI 실행 엔드포인트 수정 ---
@app.post("/run_analysis", response_model=CrewOutput)
async def run_crew_analysis(input_data: CrewInput):
    print('application operate') # 'application start'에서 'application operate'로 변경 (일관성)
    try:
        crew_instance = CrewAiDemo()
        my_crew = crew_instance.crew() # <-- 수정: my_crew = crew_instance.crew() 로 괄호 추가

        print(f"CrewAI 실행 시작 - Topic: {input_data.topic}, Company: {input_data.company_name}, Year: {input_data.current_year}, Date: {input_data.current_date}")

        crew_result = my_crew.kickoff(inputs={
            'topic': input_data.topic,
            'current_year': input_data.current_year,
            'company_name': input_data.company_name,
            'current_date': input_data.current_date # current_date 추가
        })

        # CrewAI 결과에서 JSON 문자열 추출 로직
        final_json_string = ""
        # CrewAI 0.20.x 버전 이상에서는 crew_result.raw가 직접 최종 Task의 출력 문자열을 포함합니다.
        # 이전 버전이거나 다른 이유로 raw가 없으면 tasks_outputs[-1].output을 확인합니다.
        if hasattr(crew_result, 'raw') and isinstance(crew_result.raw, str) and crew_result.raw.strip():
            final_json_string = crew_result.raw
        elif hasattr(crew_result, 'tasks_outputs') and crew_result.tasks_outputs:
            last_task_output = crew_result.tasks_outputs[-1]
            if hasattr(last_task_output, 'output') and isinstance(last_task_output.output, str) and last_task_output.output.strip():
                 final_json_string = last_task_output.output
            elif isinstance(last_task_output, str) and last_task_output.strip(): # 혹시 tasks_outputs 리스트에 직접 문자열이 들어있는 경우
                final_json_string = last_task_output
            else:
                 print(f"경고: CrewOutput.tasks_outputs[-1]의 예상치 못한 타입 또는 빈 내용: {type(last_task_output)}. 내용: {last_task_output}")

        if not final_json_string or final_json_string.strip() == "":
            print(f"경고: CrewAI 결과에서 유효한 JSON 문자열을 찾을 수 없습니다. CrewAI 결과 객체: {crew_result}")
            final_json_string = json.dumps({"error": "No valid JSON output found from CrewAI. Check agent/task output."})


        print(f"\n--- Raw JSON output from CrewAI for parsing: ---\n{final_json_string}\n--- End of Raw JSON ---\n")

        # JSON 문자열을 Pydantic 모델로 파싱
        try:
            parsed_json_report = FullAnalysisReport.model_validate_json(final_json_string)
        except Exception as e:
            print(f"JSON 파싱 또는 유효성 검사 오류: {e}. Raw JSON: {final_json_string[:500]}...")
            # Fallback to an error object for the JSON report
            # schemas.py의 FullAnalysisReport DTO 구조에 맞춰 fallback 데이터 구성
            parsed_json_report = FullAnalysisReport(
                executive_summary="Error parsing JSON report or incomplete output from AI. Please check logs.",
                introduction={"title": "Parsing Error", "content": "Failed to parse introduction content."},
                company_overview={"title": "Parsing Error", "content": "Failed to parse company overview content."},
                products_and_technology_analysis={"title": "Parsing Error",
                                                  "content": "Failed to parse products and technology content."},
                market_status_and_competition={"title": "Parsing Error",
                                               "content": "Failed to parse market status content."},
                financial_analysis={ # 재무 분석 섹션은 복잡하므로 최소한의 더미 데이터
                    "key_financial_metrics": {
                        "Q_Error": {"current_assets_USD": 0, "non_current_assets_USD": 0, "current_liabilities_USD": 0,
                                    "non_current_liabilities_USD": 0, "operating_profit_USD": 0, "net_income_USD": 0,
                                    "current_ratio": 0, "debt_to_equity_ratio": 0, "quick_ratio_estimated": 0}},
                    "changes": {"QoQ_percent_changes": {}, "YoY_percent_changes": {}},
                    "financial_insights": ["Failed to parse financial insights."]
                },
                key_risk_factors={"title": "Parsing Error", "content": "Failed to parse key risk factors content."},
                recent_news=[], # NewsItem 리스트이므로 빈 리스트
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
            json_data=parsed_json_report, # <-- 필드 이름 변경 적용
            action_command=action_command,
            message=f"CrewAI analysis complete. Command executed: {command_execution_result}"
        )

    except Exception as e:
        print(f"Error running CrewAI: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))