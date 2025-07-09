import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import re
import warnings
from datetime import datetime
import yfinance as yf
import pandas as pd # <-- pandas 임포트 추가

from dotenv import load_dotenv # <-- 추가: .env 파일 로드
load_dotenv() # <-- 추가: .env 파일 로드 함수 호출

from .crew import CrewAiDemo
from .schemas import FullAnalysisReport # FullAnalysisReport DTO 임포트 확인
from fastapi.responses import Response

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")



app = FastAPI()

class CrewInput(BaseModel):
    topic: str
    current_year: str = str(datetime.now().year)
    company_name: str
    current_date: str = datetime.now().strftime("%Y-%m-%d") # 오늘 날짜 기본값 설정

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
        return "Admin alert sent successfully."
    elif command == "initiate_data_backup":
        return "Data backup initiated."
    else:
        return f"Unknown command: {command}. No action taken."
    
def _generate_financial_markdown(financial_data: dict, company_name: str) -> str:
    """
    FinancialAnalysisSection (딕셔너리 형태) 데이터를 Markdown 보고서로 변환합니다.
    """
    markdown_output = f"## {company_name} 재무 분석\n\n"

    # 1. 재무 지표 테이블 생성
    if financial_data.get('key_financial_metrics'):
        metrics = financial_data['key_financial_metrics']
        
        df = pd.DataFrame.from_dict(metrics, orient='index')
        df.index.name = 'Quarter'
        
        markdown_output += "### 1. 분기별 주요 재무 지표 및 비율\n\n"
        markdown_output += df.to_markdown() 
        markdown_output += "\n\n"
    else:
        markdown_output += "### 1. 분기별 주요 재무 지표 및 비율\n\n데이터를 가져올 수 없습니다.\n\n"

    # 2. 비교 분석
    if financial_data.get('changes'):
        changes = financial_data['changes']
        
        markdown_output += "### 2. 재무 지표 변화 분석\n\n"
        
        markdown_output += "#### 2.1. 직전 분기 대비 변화 (QoQ)\n"
        if changes.get('QoQ_percent_changes'):
            for metric, value in changes['QoQ_percent_changes'].items():
                markdown_output += f"- **{metric}**: {value:.2f}%\n"
            markdown_output += "\n"
        else:
            markdown_output += "변화 데이터가 없습니다.\n\n"

        markdown_output += "#### 2.2. 전년 동기 대비 변화 (YoY)\n"
        if changes.get('YoY_percent_changes'):
            for metric, value in changes['YoY_percent_changes'].items():
                markdown_output += f"- **{metric}**: {value:.2f}%\n"
            markdown_output += "\n"
        else:
            markdown_output += "변화 데이터가 없습니다.\n\n"
    else:
        markdown_output += "### 2. 재무 지표 변화 분석\n\n변화 데이터를 가져올 수 없습니다.\n\n"

    # 3. 재무 인사이트
    if financial_data.get('financial_insights'):
        markdown_output += "### 3. 주요 재무 인사이트\n\n"
        for insight in financial_data['financial_insights']:
            markdown_output += f"- {insight}\n"
        markdown_output += "\n"
    else:
        markdown_output += "### 3. 주요 재무 인사이트\n\n인사이트를 가져올 수 없습니다.\n\n"

    return markdown_output

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
                content = item.get('content', {}) 

                title = content.get('title', 'N/A')
                pub_date_raw = content.get('pubDate')
                publish_date = "N/A"
                if pub_date_raw:
                    try:
                        publish_date = datetime.fromisoformat(pub_date_raw.replace('Z', '+00:00')).strftime('%Y-%m-%d')
                    except ValueError:
                        publish_date = "Invalid Date Format"
                
                source = content.get('provider', {}).get('displayName', 'N/A')
                summary = content.get('summary', 'N/A')
                url = content.get('canonicalUrl', {}).get('url', 'N/A')
                if url == 'N/A':
                    url = content.get('clickThroughUrl', {}).get('url', 'N/A')

                news_entry = {
                    "title": title,
                    "published_date": publish_date,
                    "url": url,
                    "summary": summary, # summary 필드도 다시 추가
                    "source": source # source 필드도 다시 추가
                }
                extracted_news_data.append(news_entry)

                print(f"\n--- Extracted News {i + 1} ---")
                print(f"  제목: {news_entry['title']}")
                print(f"  발행 날짜: {news_entry['published_date']}")
                print(f"  링크: {news_entry['url']}")
                if news_entry['summary']:
                    print(f"  요약: {news_entry['summary'][:200]}...")
        else:
            print(f"야후 파이낸스에서 {ticker_symbol} 뉴스를 가져올 수 없습니다.")
            extracted_news_data.append({"message": f"No news found for {ticker_symbol}."})

    except Exception as e:
        print(f"야후 파이낸스 뉴스 가져오기 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch news: {e}")
    
    return {
        "ticker": ticker_symbol,
        "extracted_news": extracted_news_data,
        "message": "News fetch attempt complete."
    }




@app.post("/run_analysis") # <-- response_model=CrewOutput 부분 제거
async def run_crew_analysis(input_data: CrewInput):
    print('application operate')
    try:
        crew_instance = CrewAiDemo()
        my_crew = crew_instance.crew() # <-- my_crew = crew_instance.crew() 로 괄호 추가

        print(f"CrewAI 실행 시작 - Topic: {input_data.topic}, Company: {input_data.company_name}, Year: {input_data.current_year}, Date: {input_data.current_date}")

        crew_result = my_crew.kickoff(inputs={
            'topic': input_data.topic,
            'current_year': input_data.current_year,
            'company_name': input_data.company_name,
            'current_date': input_data.current_date
        })

        final_json_string = ""
        if hasattr(crew_result, 'raw') and isinstance(crew_result.raw, str) and crew_result.raw.strip():
            final_json_string = crew_result.raw
        elif hasattr(crew_result, 'tasks_outputs') and crew_result.tasks_outputs:
            last_task_output = crew_result.tasks_outputs[-1]
            if hasattr(last_task_output, 'output') and isinstance(last_task_output.output, str) and last_task_output.output.strip():
                 final_json_string = last_task_output.output
            elif isinstance(last_task_output, str) and last_task_output.strip():
                final_json_string = last_task_output
            else:
                 print(f"경고: CrewOutput.tasks_outputs[-1]의 예상치 못한 타입 또는 빈 내용: {type(last_task_output)}. 내용: {last_task_output}")

        if not final_json_string or final_json_string.strip() == "":
            print(f"경고: CrewAI 결과에서 유효한 JSON 문자열을 찾을 수 없습니다. CrewAI 결과 객체: {crew_result}")
            final_json_string = json.dumps({"error": "No valid JSON output found from CrewAI. Check agent/task output."})

        print(f"\n--- Raw JSON output from CrewAI for parsing: ---\n{final_json_string}\n--- End of Raw JSON ---\n")

        try:
            return Response(content=final_json_string, media_type="application/json")

        except Exception as e:
            # JSON 파싱 실패 시, 에러 JSON을 직접 반환
            print(f"JSON 파싱 또는 유효성 검사 오류: {e}. Raw JSON: {final_json_string[:500]}...")
            import traceback
            traceback.print_exc()
            error_response_content = json.dumps({"status": "error", "message": f"Failed to parse CrewAI JSON output: {e}"})
            return Response(content=error_response_content, media_type="application/json", status_code=500)

    except Exception as e:
        print(f"Error running CrewAI: {e}")
        import traceback
        traceback.print_exc()
        error_response_content = json.dumps({"status": "error", "message": f"Error during CrewAI execution: {e}"})
        return Response(content=error_response_content, media_type="application/json", status_code=500)
