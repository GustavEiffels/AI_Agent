from typing import Dict
from ai_test.jh_crew import SbtProject
from fastapi import FastAPI, BackgroundTasks
import asyncio
import json

app = FastAPI()

async def run_crew_process(inputs: dict) -> Dict:
    try:
        # The kickoff method returns the raw string output of the final task.
        raw_result_string = await asyncio.to_thread(SbtProject().crew().kickoff, inputs=inputs)
        print(f'Raw result string from CrewAI: {raw_result_string}') # Print raw string for debugging

        # Attempt to parse the string as JSON
        try:
            parsed_result = json.loads(raw_result_string)
            print("\nCrewAI process completed successfully and JSON parsed.")
            return parsed_result
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            print(f"Attempting to extract JSON block from raw string...")
            # If direct parse fails, try to find a JSON block
            import re
            json_match = re.search(r'```json\n(.*?)```', raw_result_string, re.DOTALL)
            if json_match:
                json_string = json_match.group(1)
                try:
                    parsed_result = json.loads(json_string)
                    print("\nSuccessfully extracted and parsed JSON block.")
                    return parsed_result
                except json.JSONDecodeError as inner_e:
                    print(f"Error parsing extracted JSON block: {inner_e}")
                    return {"error": "Failed to parse JSON even after extraction attempt", "raw_output": raw_result_string}
            else:
                return {"error": "Failed to parse JSON and no JSON block found", "raw_output": raw_result_string}

    except Exception as e:
        print(f"\nAn error occurred while running the CrewAI process in background: {e}")
        return {"error": str(e), "raw_output": "Process failed before JSON parsing."}

@app.get("/run_crewai_task")
async def start_crewai_task(background_tasks: BackgroundTasks):
    print('API Endpoint Called: Starting CrewAI process...')

    inputs = {
        'company': '현대자동차',
        'sales_activity': {
            "activity":
            [
                {
                    "ActivityDate": "2024-06-09",
                    "Subject": "공고",
                    "Description": "• 사업기간 : 2024년 10월 ~ 2025년 9월 (12개월)\n• 사업예산 : 약 80억원\n• 사업일정 : 2024년 7월 공고 예정 / 9월말 계약 예상\n• 예상경쟁 : KL정보통신, 하이밸류 등\n• 영업전략 : 메가존과 컨소시엄으로 CRM 고도화 부문 수행 (기존 컨버젼 컨소시엄)\n• 추진계획 : - 공단 요구사항 확인 및 투입계획 작성\n                                - 메가존과 컨소시엄 구도 협의"
                },
                {
                    "ActivityDate": "2024-06-23",
                    "Subject": "Call",
                    "Description": "메가존과 사업 참여 컨소시엄 구성 협의"
                },
                {
                    "ActivityDate": "2024-08-11",
                    "Subject": "CRM 고도화 RFP 검토 미팅",
                    "Description": "CRM 고도화 사업 제안요청서 요구사항 검토\n수정 및 변경 내용 반영 요청"
                },
                {
                    "ActivityDate": "2024-09-01",
                    "Subject": "사업 제안 준비",
                    "Description": "주사업자(메가존)와 사업 수행 방안 협의 진행\n컨소시엄 확정 완료\n금주 본 사업 공고 예상\nCRM 부문 제안 작업 준비"
                },
                {
                    "ActivityDate": "2024-09-15",
                    "Subject": "주간 보고",
                    "Description": "RFP 내부 감사 승인의 지연으로 이번 주 공고 예정\n제안팀 구성 및 제안서 작성"
                },
                {
                    "ActivityDate": "2024-09-29",
                    "Subject": "주간 보고",
                    "Description": "국정 감사로 인하여 발주 지연\n이번 주 공고 예정\n제안팀 구성 및 제안서 작성"
                },
                {
                    "ActivityDate": "2024-10-13",
                    "Subject": "주간 보고",
                    "Description": "계약처에서 공고 지연\n이번 주 공고 예정\n제안서 초안을 메가존에 전달 예정"
                },
                {
                    "ActivityDate": "2024-10-20",
                    "Subject": "주간 보고",
                    "Description": "10/12 사업 공고\n11/30 입찰 마감\n10/18 (수) 제안요청설명회\n메가존 컨소시엄으로 참여 / 제안서 작성중."
                },
                {
                    "ActivityDate": "2024-11-02",
                    "Subject": "주간 보고",
                    "Description": "제안 요청 설명회 참석\n제안서 및 수행 업무 범위 협의 w/메가존 컨소시엄"
                },
                {
                    "ActivityDate": "2024-11-17",
                    "Subject": "주간 보고",
                    "Description": "11/30 입찰 마감으로 메가존 / KL정보 / SBT 컨소시엄으로 제안 참여\n제안서 작성 및 수행 방안 협의 중"
                },
                {
                    "ActivityDate": "2024-12-08",
                    "Subject": "사업 공고 일정",
                    "Description": "11/30 사업 유찰 : 단독 응찰\n재공고 일정 확인 (이번 주초 예상)"
                },
                {
                    "ActivityDate": "2024-12-15",
                    "Subject": "1차 유찰 및 재공고",
                    "Description": "11/30 유찰 : 단독 응찰\n12/1 재공고\n12/14 입찰 참가 신청\n12/15 제안 제출 마감\n12/21 개찰\n24년 1월 초 계약 예상\n예산 부족으로 수행 전략 및 금액 협의 중"
                },
                {
                    "ActivityDate": "2024-12-22",
                    "Subject": "CRM 고도화 재공고 유찰",
                    "Description": "12/15 제안서 제출 / 재공고 유찰 : 단독 응찰\n제안 발표 예정\n기술 협상시 인력투입 계획 및 EP 구현 범위에 대한 이슈 협의"
                },
                {
                    "ActivityDate": "2025-01-12",
                    "Subject": "CRM 고도화 기술 협상 완료",
                    "Description": "CRM 고도화 사업의 기술협상 완료\n이번 주 가격 협상 예정\n다음 주 계약 진행"
                },
                {
                    "ActivityDate": "2025-01-19",
                    "Subject": "계약 가격 협상",
                    "Description": "현재 가격 협상중이나 협의 어려움\n계약처에서 2차 가격 연장 요청 (10일)\n협상이 안 될 경우 사업 재설계 / 재공고 가능성 있음"
                },
                {
                    "ActivityDate": "2025-01-25",
                    "Subject": "가격 협상 2차 연장",
                    "Description": "1/25까지 가격 협상 마지막 연장\n협상 결렬시 - 사업 재설계 후 공고\n정보관리처와 협의 중"
                },
                {
                    "ActivityDate": "2025-02-02",
                    "Subject": "최종 제안 금액 투찰",
                    "Description": "최종 금액 투찰 - 계약처와 정보관리처 협의 중"
                },
                {
                    "ActivityDate": "2025-02-09",
                    "Subject": "사업 재공고",
                    "Description": "지난 주 계약처로부터 가격 협상 결렬 통보\n이번 주 초 재공고 예정\n담당자와 업무 범위 협의 진행"
                },
                {
                    "ActivityDate": "2025-02-23",
                    "Subject": "사업 설명회",
                    "Description": "2/15 사업 입찰 공고 (3/28 제안 입찰 마감)\n2/16 제안 요청 설명회"
                },
                {
                    "ActivityDate": "2025-03-22",
                    "Subject": "사업 입찰 준비",
                    "Description": "3/28 제안 마감\n경쟁 입찰 여부 모니터링\n수의 시담에 대비한 컨소시엄 협의"
                },
                {
                    "ActivityDate": "2025-04-05",
                    "Subject": "Call",
                    "Description": "3/28 입찰 마감\n3/29 (금) 제안 발표\nVTW 경쟁으로 입찰 참가\n이번 주 우선협상 대상자 선정"
                },
                {
                    "ActivityDate": "2025-04-12",
                    "Subject": "Call",
                    "Description": "4/4 정보관리처장 미팅\n4/9 기술협상 완료 예정\n4/15 계약 완료 예정"
                },
                {
                    "ActivityDate": "2025-04-19",
                    "Subject": "Call",
                    "Description": "기술 협상 및 가격 협상 완료\n이번 주 계약 예상\n컨소시엄사 금액 협의 및 확정"
                },
                {
                    "ActivityDate": "2025-05-03",
                    "Subject": "Call",
                    "Description": "지난 주 국가철도공단 계약 완료\n착수계 및 수행인력 계약 진행"
                },
                {
                    "ActivityDate": "2025-05-10",
                    "Subject": "Call",
                    "Description": "5/3 금 : 공단 조직 개편으로 디지털융합처 처장, 부장 미팅\n착수계 서류 준비"
                },
                {
                    "ActivityDate": "2025-05-31",
                    "Subject": "Call",
                    "Description": "5/30 착수보고회 예정"
                },
                {
                    "ActivityDate": "2025-06-07",
                    "Subject": "Call",
                    "Description": "5/30 착수보고회\n대금 지급 조건 협의 중"
                },
                {
                    "ActivityDate": "2025-06-14",
                    "Subject": "Call",
                    "Description": "- 2025년 매출 계획 12억 (SBT 영역, VAT포함)\n- 12억원의 40% 선금 신청 예정 (6월 말까지)"
                },
                {
                    "ActivityDate": "2025-06-21",
                    "Subject": "Call",
                    "Description": "6/11 국가철도공단 착수 회식\n24년 13억 (VAT 별도) 세금 계산서 / 선금 5억 진행"
                },
                {
                    "ActivityDate": "2025-06-28",
                    "Subject": "Call",
                    "Description": "대금 지급 조건 확정 및 선금 신청\n인천항만공사 벤치마킹 방문"
                },
                {
                    "ActivityDate": "2025-07-01",
                    "Subject": "신제품 소개 미팅",
                    "Description": "신제품 소개 미팅"
                }
            ]
        }
    }

    print(f'Inputs for CrewAI: {inputs}')
    final_output = await run_crew_process(inputs)
    return final_output
