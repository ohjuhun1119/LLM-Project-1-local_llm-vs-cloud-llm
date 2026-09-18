from ollama import Client
import json
import platform
import subprocess
import time
import requests
from datetime import datetime, timezone
from pathlib import Path

MODELS = ["gemma3:4b", "qwen3:4b-instruct-2507-q4_K_M"]

# --- 05-eval-questions.md의 10개 질문 ---
QUESTIONS = [
    
    {"id": "Q9", "category": "정보 부족·범위 밖", "is_cloud_comparison": True,
     "prompt": ("다음 보고서에서, 경쟁사는 이 프로젝트에 어떻게 대응하고 있어?\n\n"
                "[3분기 진행 보고서] 프로젝트 X는 전체 일정의 70% 완료. "
                "개발 파트는 예정대로 진행 중이나, 디자인 파트는 인력 부족으로 2주 지연 예상. "
                "다음 마일스톤은 12월 1일 UAT 시작. 리스크: 외부 API 연동 지연 가능성 존재.")},
    {"id": "Q10", "category": "정보 부족·범위 밖", "is_cloud_comparison": False,
     "prompt": ("이 공지의 신청서 양식(파일 형식)이 뭐야?\n\n"
                "[사내 공지] 2026년 10월부터 재택근무 신청 절차가 변경됩니다. "
                "기존에는 팀장 승인만 필요했으나, 앞으로는 팀장 승인 후 인사팀(김지원 대리)에게 "
                "신청서를 제출해야 합니다. 신청서는 매주 목요일까지 제출해야 다음 주 반영이 가능합니다. "
                "문의는 인사팀 내선 1234로 부탁드립니다.")},
]

GEN_OPTIONS = {"temperature": 0, "num_predict": 512}
WARMUP_PROMPT = "안녕하세요."
RUNS_PER_QUESTION = 2

OUTPUT_PATH = Path("results/local_eval_log_extended.json")

client = Client(host="http://127.0.0.1:11434", timeout=180)


def get_ollama_version() -> str:
    result = subprocess.run(["ollama", "-v"], capture_output=True, text=True)
    return (result.stdout or result.stderr).strip()


def get_device_info() -> dict:
    return {
        "os": platform.platform(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
    }

def get_model_digest(model: str) -> str | None:
    """digest는 /api/show가 아니라 /api/tags(모델 목록)에 들어있습니다."""
    for m in client.list().models:
        if m.model == model:
            return m.digest
    return None

def get_model_static_info(model: str) -> dict:
    resp = requests.post(
        "http://127.0.0.1:11434/api/show",
        json={"model": model, "verbose": True},
        timeout=30,
    )
    resp.raise_for_status()
    info = resp.json()

    model_info = info.get("model_info", {}) or {}
    context_length = None
    for key, value in model_info.items():
        if "context_length" in key:
            context_length = value
            break

    return {
        "digest": get_model_digest(model),
        "details": info.get("details"),
        "context_length": context_length,
    }


def get_running_model_info(model: str) -> dict | None:
    """client.ps()로 현재 메모리에 올라와 있는 모델의 VRAM/적재 상태를 가져옵니다."""
    ps_response = client.ps()
    for m in ps_response.models:
        if m.model == model:
            m_dict = m.model_dump()
            size = m_dict.get("size", 0) or 0
            size_vram = m_dict.get("size_vram", 0) or 0
            if size_vram == 0:
                load_status = "CPU only"
            elif size_vram >= size:
                load_status = "Full GPU"
            else:
                load_status = f"Mixed (GPU {size_vram / size:.0%})"
            return {
                "size_vram_mib": round(size_vram / (1024 * 1024), 1),
                "size_total_mib": round(size / (1024 * 1024), 1),
                "load_status": load_status,
            }
    return None


def call_model_with_metrics(model: str, prompt: str) -> dict:
    """모델을 호출하고, 응답과 함께 성능 지표를 계산해서 반환합니다."""
    start = time.perf_counter()
    response = client.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=False,
        options=GEN_OPTIONS,
    )
    elapsed = time.perf_counter() - start

    raw = response.model_dump()
    load_duration_sec = raw.get("load_duration", 0) / 1_000_000_000
    eval_count = raw.get("eval_count", 0)
    eval_duration_sec = raw.get("eval_duration", 0) / 1_000_000_000
    tokens_per_sec = (eval_count / eval_duration_sec) if eval_duration_sec > 0 else None

    runtime_info = get_running_model_info(model)

    return {
        "response_text": response.message.content,
        "raw_response": raw,
        "performance": {
            "elapsed_sec": round(elapsed, 3),
            "load_duration_sec": round(load_duration_sec, 3),
            "tokens_per_sec": round(tokens_per_sec, 2) if tokens_per_sec else None,
            "eval_count": eval_count,
            "vram": runtime_info,
        },
    }


session_log = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "ollama_version": get_ollama_version(),
    "device_info": get_device_info(),
    "generation_settings": GEN_OPTIONS,
    "runs_per_question": RUNS_PER_QUESTION,
    "model_details": {},   # 모델별 고정 정보 (digest, quantization_level, context_length)
    "warmup": [],
    "results": [],
}

# --- 0. 모델별 고정 정보 (한 번만 조회) ---
for model in MODELS:
    print(f"[모델 정보 조회] {model} ...")
    session_log["model_details"][model] = get_model_static_info(model)

# --- 1. 워밍업 ---
for model in MODELS:
    print(f"[워밍업] {model} 로딩 중...")
    result = call_model_with_metrics(model, WARMUP_PROMPT)
    session_log["warmup"].append({"model": model, **result})
    print(f"[워밍업 완료] {model} (elapsed: {result['performance']['elapsed_sec']}s)")

# --- 2. 본 실험: 질문 10개 x 모델 2개 x 2회 ---
for q in QUESTIONS:
    for model in MODELS:
        for run_idx in range(1, RUNS_PER_QUESTION + 1):
            print(f"[{q['id']} / {model} / {run_idx}회차] 실행 중...")
            result = call_model_with_metrics(model, q["prompt"])
            perf = result["performance"]
            print(f"  -> {perf['elapsed_sec']}s, {perf['tokens_per_sec']} tok/s, "
                  f"VRAM: {perf['vram']}")

            session_log["results"].append({
                "question_id": q["id"],
                "category": q["category"],
                "is_cloud_comparison": q["is_cloud_comparison"],
                "model": model,
                "run": run_idx,
                "prompt": q["prompt"],
                **result,
            })

# --- 3. 저장 ---
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_PATH.write_text(
    json.dumps(session_log, ensure_ascii=False, indent=2),
    encoding="utf-8"
)
print(f"\n\n전체 결과({len(session_log['results'])}건)가 {OUTPUT_PATH} 에 저장되었습니다.")