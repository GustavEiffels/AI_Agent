import warnings
import traceback
import json
from datetime import datetime
from ai_test.hs_crew import SalesforceCrewai
from dotenv import load_dotenv
from fastapi import FastAPI, BackgroundTasks  # BackgroundTasks 임포트 추가
import asyncio

app = FastAPI()
load_dotenv()

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


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

        if isinstance(raw_summary_string_from_output, str) and \
                raw_summary_string_from_output.startswith("'") and raw_summary_string_from_output.endswith("'"):
            raw_summary_string_from_output = raw_summary_string_from_output[1:-1]

        try:
            final_parsed_list = json.loads(raw_summary_string_from_output)
        except json.JSONDecodeError:
            final_parsed_list = raw_summary_string_from_output
            print("Warning: CrewOutput.raw was already a list/dict in background, no JSON parsing needed.")

        print(f'Final Parsed List (Background): {final_parsed_list}')


    except Exception as e:
        print(f"Background CrewAI error at {datetime.now()}: {e}")
        traceback.print_exc()


@app.get('/hs_test')
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