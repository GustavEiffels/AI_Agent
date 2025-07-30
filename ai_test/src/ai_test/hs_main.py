import warnings
import traceback
import json
from datetime import datetime
from ai_test.hs_crew import SalesforceCrewai
from dotenv import load_dotenv
from fastapi import FastAPI

# CrewOutput 타입을 명시적으로 임포트하는 것이 좋습니다.
# from crewai.schemas import CrewOutput # crewai 버전에 따라 경로가 다를 수 있습니다.
# 만약 CrewOutput을 임포트할 수 없다면, 단순히 .raw 속성 접근으로 충분할 수 있습니다.

app = FastAPI()
load_dotenv()

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


@app.get('/hs_test')
async def hs_test():
    print("inputs 실행 성공>>")
    current_year = str(datetime.now().year)
    inputs = {'current_year': current_year}
    try:
        print("inputs 실행 성공:", inputs)
        salesforce_crew = SalesforceCrewai()

        crew_output_object = salesforce_crew.run(inputs=inputs)

        print(f'CrewOutput Object Type: {type(crew_output_object)}')
        print(f'CrewOutput Object Raw Content: {crew_output_object.raw}')  # raw 속성 확인

        raw_summary_string_from_output = crew_output_object.raw
        if isinstance(raw_summary_string_from_output, str) and \
                raw_summary_string_from_output.startswith("'") and raw_summary_string_from_output.endswith("'"):
            raw_summary_string_from_output = raw_summary_string_from_output[1:-1]
            print(f'Cleaned Raw Summary String from Output: {raw_summary_string_from_output}')

        try:
            final_parsed_list = json.loads(raw_summary_string_from_output)
        except json.JSONDecodeError as json_err:
            print(f"JSON Decode Error inside hs_test: {json_err}")
            if isinstance(raw_summary_string_from_output, (list, dict)):  # 이미 리스트나 딕셔너리면 그대로 사용
                final_parsed_list = raw_summary_string_from_output
                print("Warning: CrewOutput.raw was already a list/dict, no JSON parsing needed.")
            else:
                raise  # JSON 파싱이 안되는 문자열이거나 아예 다른 타입이면 에러를 던집니다.

        print(f'Final Parsed List: {final_parsed_list}')

        return {'result': final_parsed_list}

    except Exception as e:
        print(f"에러 발생: {e}")
        traceback.print_exc()
        raise