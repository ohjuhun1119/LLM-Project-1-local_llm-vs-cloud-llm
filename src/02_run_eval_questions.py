from ollama import Client
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

MODELS = ["gemma3:4b", "qwen3:4b-instruct-2507-q4_K_M"]

# --- 05-eval-questions.md의 10개 질문 ---
# is_cloud_comparison: True로 표시된 5개는 STEP 5에서 결과를 보기 전에 미리 선정한
# Cloud API 비교용 질문입니다 (Q1, Q3, Q5, Q6, Q9).
QUESTIONS = [
    {
        "id": "Q1",
        "category": "정상 사례",
        "is_cloud_comparison": True,
        "prompt": (
            "다음 공지사항을 요약해줘.\n\n"
            "[사내 공지] 2026년 10월부터 재택근무 신청 절차가 변경됩니다. "
            "기존에는 팀장 승인만 필요했으나, 앞으로는 팀장 승인 후 인사팀(김지원 대리)에게 "
            "신청서를 제출해야 합니다. 신청서는 매주 목요일까지 제출해야 다음 주 반영이 가능합니다. "
            "문의는 인사팀 내선 1234로 부탁드립니다."
        ),
    },
    {
        "id": "Q2",
        "category": "정상 사례",
        "is_cloud_comparison": False,
        "prompt": (
            "다음 회의록을 요약해줘.\n\n"
            "[주간 회의록] 참석자: 박민수 팀장, 이서연 대리, 최동훈 사원. "
            "신제품 A의 출시일을 11월 15일로 확정. 이서연 대리가 마케팅 자료 초안을 "
            "11월 1일까지 작성하기로 함. 최동훈 사원은 협력사 견적서를 다음 주까지 수합. "
            "다음 회의는 10월 20일 예정."
        ),
    },
    {
        "id": "Q3",
        "category": "정상 사례",
        "is_cloud_comparison": True,
        "prompt": (
            "다음 진행 보고서를 요약해줘.\n\n"
            "[3분기 진행 보고서] 프로젝트 X는 전체 일정의 70% 완료. "
            "개발 파트는 예정대로 진행 중이나, 디자인 파트는 인력 부족으로 2주 지연 예상. "
            "다음 마일스톤은 12월 1일 UAT 시작. 리스크: 외부 API 연동 지연 가능성 존재."
        ),
    },
    {
        "id": "Q4",
        "category": "경계 사례",
        "is_cloud_comparison": False,
        "prompt": (
            "다음 회의록을 요약해줘.\n\n"
            "[태스크포스 회의록] A안건 담당 이하늘(9/20 마감), B안건 담당 정우진(9/25 마감), "
            "C안건은 담당자 미정 상태로 다음 회의에서 재논의하기로 함. "
            "김수현 부장은 전체 일정을 10/1로 앞당길 것을 요청함."
        ),
    },
    {
        "id": "Q5",
        "category": "경계 사례",
        "is_cloud_comparison": True,
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
        "is_cloud_comparison": True,
        "prompt": (
            "다음 회의록의 결정사항과 액션 아이템을 표(담당자/내용/기한)로 정리해줘.\n\n"
            "[주간 회의록] 참석자: 박민수 팀장, 이서연 대리, 최동훈 사원. "
            "신제품 A의 출시일을 11월 15일로 확정. 이서연 대리가 마케팅 자료 초안을 "
            "11월 1일까지 작성하기로 함. 최동훈 사원은 협력사 견적서를 다음 주까지 수합. "
            "다음 회의는 10월 20일 예정."
        ),
    },
    {
        "id": "Q7",
        "category": "경계 사례",
        "is_cloud_comparison": False,
        "prompt": "다음 공지사항을 요약해줘.\n\n[공지] 내일 오전 10시 전체 회의 있습니다.",
    },
    {
        "id": "Q8",
        "category": "정보 부족·범위 밖",
        "is_cloud_comparison": False,
        "prompt": (
            "다음 회의록에서 논의된 예산 규모를 알려줘.\n\n"
            "[주간 회의록] 참석자: 박민수 팀장, 이서연 대리, 최동훈 사원. "
            "신제품 A의 출시일을 11월 15일로 확정. 이서연 대리가 마케팅 자료 초안을 "
            "11월 1일까지 작성하기로 함. 최동훈 사원은 협력사 견적서를 다음 주까지 수합. "
            "다음 회의는 10월 20일 예정."
        ),
    },
    {
        "id": "Q9",
        "category": "정보 부족·범위 밖",
        "is_cloud_comparison": True,
        "prompt": (
            "다음 보고서에서, 경쟁사는 이 프로젝트에 어떻게 대응하고 있어?\n\n"
            "[3분기 진행 보고서] 프로젝트 X는 전체 일정의 70% 완료. "
            "개발 파트는 예정대로 진행 중이나, 디자인 파트는 인력 부족으로 2주 지연 예상. "
            "다음 마일스톤은 12월 1일 UAT 시작. 리스크: 외부 API 연동 지연 가능성 존재."
        ),
    },
    {
        "id": "Q10",
        "category": "정보 부족·범위 밖",
        "is_cloud_comparison": False,
        "prompt": (
            "이 공지의 신청서 양식(파일 형식)이 뭐야?\n\n"
            "[사내 공지] 2026년 10월부터 재택근무 신청 절차가 변경됩니다. "
            "기존에는 팀장 승인만 필요했으나, 앞으로는 팀장 승인 후 인사팀(김지원 대리)에게 "
            "신청서를 제출해야 합니다. 신청서는 매주 목요일까지 제출해야 다음 주 반영이 가능합니다. "
            "문의는 인사팀 내선 1234로 부탁드립니다."
        ),
    },
]

GEN_OPTIONS = {"temperature": 0, "num_predict": 256}
WARMUP_PROMPT = "안녕하세요."  # 모델 로딩(콜드 스타트) 영향을 없애기 위한 워밍업용 질문
RUNS_PER_QUESTION = 2  # 질문당 반복 횟수 (모델당 총 10문항 x 2회 = 20회)

OUTPUT_PATH = Path("results/local_eval_log.json")

client = Client(host="http://127.0.0.1:11434", timeout=180)


def get_ollama_version() -> str:
    """설치된 Ollama 버전을 확인합니다."""
    result = subprocess.run(["ollama", "-v"], capture_output=True, text=True)
    return (result.stdout or result.stderr).strip()


def get_device_info() -> dict:
    """현재 실행 장비 정보를 기록합니다."""
    return {
        "os": platform.platform(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
    }


def call_model(model: str, prompt: str):
    """Ollama에 질문을 보내고 응답 객체를 그대로 반환합니다."""
    return client.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=False,
        options=GEN_OPTIONS,
    )


session_log = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "ollama_version": get_ollama_version(),
    "device_info": get_device_info(),
    "generation_settings": GEN_OPTIONS,
    "runs_per_question": RUNS_PER_QUESTION,
    "warmup": [],   # 본 비교 집계에서 제외되는 워밍업 기록
    "results": [],  # 본 실험 기록 (모델당 20회)
}

# --- 1. 워밍업: 모델당 1회, 본 집계와 분리하여 기록 ---
for model in MODELS:
    print(f"[워밍업] {model} 로딩 중...")
    response = call_model(model, WARMUP_PROMPT)
    session_log["warmup"].append({
        "model": model,
        "response_text": response.message.content,
        "raw_response": response.model_dump(),
    })
    print(f"[워밍업 완료] {model}")

# --- 2. 본 실험: 질문 10개 x 모델 2개 x 2회 = 모델당 20회 ---
for q in QUESTIONS:
    for model in MODELS:
        for run_idx in range(1, RUNS_PER_QUESTION + 1):
            print(f"[{q['id']} / {model} / {run_idx}회차] 실행 중...")
            response = call_model(model, q["prompt"])
            print(f"  -> {response.message.content[:50]}...")

            session_log["results"].append({
                "question_id": q["id"],
                "category": q["category"],
                "is_cloud_comparison": q["is_cloud_comparison"],
                "model": model,
                "run": run_idx,
                "prompt": q["prompt"],
                "response_text": response.message.content,
                "raw_response": response.model_dump(),
            })

# --- 3. 결과 저장 ---
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_PATH.write_text(
    json.dumps(session_log, ensure_ascii=False, indent=2),
    encoding="utf-8"
)
print(f"\n\n전체 결과({len(session_log['results'])}건)가 {OUTPUT_PATH} 에 저장되었습니다.")