from fastapi import FastAPI, Request, BackgroundTasks
from pydantic import BaseModel
from uuid import uuid4
from ai_test.gs_crew import AbmAi
import os, json
import requests

app = FastAPI()
RESULT_DIR = "results"
# 요청받을 데이터 구조 정의
class ABMRequest(BaseModel):
    AccountName: str
    AnnualRevenue: str
    Industry: str

# Serper 검색 결과 함수 (선택사항)
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

@app.post("/run-abm")
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

@app.get("/result/{job_id}")
async def get_abm_result(job_id: str):
    path = f"{RESULT_DIR}/{job_id}.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return {"status": "complete", "result": json.load(f)}
    else:
        return {"status": "pending"}