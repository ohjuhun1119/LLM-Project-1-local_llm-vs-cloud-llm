from getpass import getpass
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from openai import APIError, APITimeoutError, OpenAI

QUESTIONS =[
    {
        "id": "Q1",
        "category": "정상 사례",
        "prompt": (
            "다음 공지사항을 요약해줘.\n\n"
            "[사내 공지] 2026년 10월부터 재택근무 신청 절차가 변경됩니다. "
            "기존에는 팀장 승인만 필요했으나, 앞으로는 팀장 승인 후 인사팀(김지원 대리)에게 "
            "신청서를 제출해야 합니다. 신청서는 매주 목요일까지 제출해야 다음 주 반영이 가능합니다. "
            "문의는 인사팀 내선 1234로 부탁드립니다."
        ),
    },
    {
        "id": "Q3",
        "category": "정상 사례",
        "prompt": (
            "다음 진행 보고서를 요약해줘.\n\n"
            "[3분기 진행 보고서] 프로젝트 X는 전체 일정의 70% 완료. "
            "개발 파트는 예정대로 진행 중이나, 디자인 파트는 인력 부족으로 2주 지연 예상. "
            "다음 마일스톤은 12월 1일 UAT 시작. 리스크: 외부 API 연동 지연 가능성 존재."
        ),
    },
    {
        "id": "Q5",
        "category": "경계 사례",
        "prompt": (
            "다음 프로젝트 업데이트를 요약해줘.\n\n"
            "[프로젝트 업데이트] 초안에서는 예산이 5천만 원으로 책정되었으나, "
            "회의 중 재무팀 검토 결과 4천 2백만 원으로 하향 조정됨. "
            "최종 승인된 예산은 4천 2백만 원임."
        ),
    },
    {
        "id": "Q6",
        "category": "경계 사례",
        "prompt": (
            "다음 회의록의 결정사항과 액션 아이템을 표(담당자/내용/기한)로 정리해줘.\n\n"
            "[주간 회의록] 참석자: 박민수 팀장, 이서연 대리, 최동훈 사원. "
            "신제품 A의 출시일을 11월 15일로 확정. 이서연 대리가 마케팅 자료 초안을 "
            "11월 1일까지 작성하기로 함. 최동훈 사원은 협력사 견적서를 다음 주까지 수합. "
            "다음 회의는 10월 20일 예정."
        ),
    },
    {
        "id": "Q9",
        "category": "정보 부족·범위 밖",
        "prompt": (
            "다음 보고서에서, 경쟁사는 이 프로젝트에 어떻게 대응하고 있어?\n\n"
            "[3분기 진행 보고서] 프로젝트 X는 전체 일정의 70% 완료. "
            "개발 파트는 예정대로 진행 중이나, 디자인 파트는 인력 부족으로 2주 지연 예상. "
            "다음 마일스톤은 12월 1일 UAT 시작. 리스크: 외부 API 연동 지연 가능성 존재."
        ),
    },
]

PRICE_PER_TOKEN_INPUT = 0.0000002
PRICE_PER_TOKEN_OUTPUT = 0.0000012

OUTPUT_PATH = Path("results/luna_eval_log.json")

api_key = getpass("OpenAI API 키를 붙여넣고 ENTER (화면에 보이지 않음):").strip()
if not api_key:
    raise SystemExit("키를 입력하지 않아 API를 호출하지 않았습니다.")

client = OpenAI(
    api_key = api_key,
    base_url="https://api.openai.com/v1",
    timeout=60,
    max_retries=0,
)

def estimate_cost(input_tokens: int, output_tokens: int) -> dict:
    cost = (
        input_tokens * PRICE_PER_TOKEN_INPUT
        + output_tokens * PRICE_PER_TOKEN_OUTPUT
    )
    return {"estimate_cost_usd": round(cost, 6)}

def call_luna(prompt: str) -> dict:
    start = time.perf_counter()
    try:
        response = client.responses.create(
            model="gpt-5.6-luna",
            input=prompt,
            reasoning={"effort": "none"},
            max_output_tokens=256,
            tools=[],
            tool_choice="none",
            store=False,
        )
        elapsed = time.perf_counter() - start
        usage = response.usage
        input_tokens = usage.input_tokens
        output_tokens = usage.output_tokens

        return {
            "status":"success",
            "response_text": response.output_text,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "elapsed":elapsed,
            "cost": estimate_cost(input_tokens, output_tokens),
            "error_message": None,
        }
    except APITimeoutError:
        elapsed = time.perf_counter() - start
        return {
            "status": "error_time_out",
            "response_text": None,
            "input_tokens": None,
            "output_tokens": None,
            "elapsed":elapsed,
            "cost":None,
            "error_message": "응답 대기 시간 초과",
        }
    except APIError as error:
        elapsed = time.perf_counter() - start
        status = getattr(error, "status_code", "연결 오류")
        return {
            "status": "error_API",
            "response_text": None,
            "input_tokens": None,
            "output_tokens": None,
            "elapsed":elapsed,
            "cost":None,
            "error_message": f"API 호출 실패,{status}",
        }
session_log = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "model":"gpt-5.6-luna",
    "generation_settings": {
        "max_output_tokens": 256,
    },
    "runs_cloud":1,
    "runs_local":2,
    "results":[]
}

success_count = 0
total_count = len(QUESTIONS)

for q in QUESTIONS:
    print(f"{q['id']} Luna에 질문을 보냈습니다. 답변을 기다려 주세요.")
    result = call_luna(q["prompt"])

    if result["status"] =="success":
        success_count += 1
        print("성공")
    else:
        print(f"실패,{result['error_message']}")

    session_log["results"].append({
        "question_id":q["id"],
        "model": "gpt-5.6-luna",
        "run": 1,
        "prompt": q["prompt"],
        **result,
    })

session_log["성공 비율"] = f"{success_count}/{total_count}"

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_PATH.write_text(
    json.dumps(session_log, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print(f"결과가 {OUTPUT_PATH}에 저장되었습니다.")
