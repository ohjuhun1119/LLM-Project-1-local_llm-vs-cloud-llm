from ollama import Client
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

QUESTION = (
    "다음 공지사항을 요약해줘.\n\n"
    "[사내 공지] 2026년 10월부터 재택근무 신청 절차가 변경됩니다. "
    "기존에는 팀장 승인만 필요했으나, 앞으로는 팀장 승인 후 인사팀(김지원 대리)에게 "
    "신청서를 제출해야 합니다. 신청서는 매주 목요일까지 제출해야 다음 주 반영이 가능합니다. "
    "문의는 인사팀 내선 1234로 부탁드립니다."
)
GEN_OPTIONS = {"temperature": 0, "num_predict": 256}
OUTPUT_PATH = Path("results/environment_check_log.json")

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

print("[gemma3:4b]에 질문을 보냈습니다. 답변을 기다려 주세요.")
response_gemma = client.chat(
    model="gemma3:4b",
    messages=[{"role": "user", "content": QUESTION}],
    stream=False,
    options=GEN_OPTIONS,
)
print("\n[gemma3:4b 답변]")
print(response_gemma.message.content)

print("\n[qwen3:4b-instruct-2507-q4_K_M]에 질문을 보냈습니다. 답변을 기다려 주세요.")
response_qwen = client.chat(
    model="qwen3:4b-instruct-2507-q4_K_M",
    messages=[{"role": "user", "content": QUESTION}],
    stream=False,
    options=GEN_OPTIONS,
)
print("\n[qwen3:4b-instruct-2507-q4_K_M 답변]")
print(response_qwen.message.content)

# --- 버전 / 장비 / 설정 / 원본 기록을 JSON 파일로 저장 ---
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

session_log = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "ollama_version": get_ollama_version(),
    "device_info": get_device_info(),
    "generation_settings": GEN_OPTIONS,
    "question": QUESTION,
    "results": [
        {
            "model": "gemma3:4b",
            "response_text": response_gemma.message.content,
            "raw_response": response_gemma.model_dump(),
        },
        {
            "model": "qwen3:4b-instruct-2507-q4_K_M",
            "response_text": response_qwen.message.content,
            "raw_response": response_qwen.model_dump(),
        },
    ],
}

OUTPUT_PATH.write_text(
    json.dumps(session_log, ensure_ascii=False, indent=2),
    encoding="utf-8"
)
print(f"\n결과가 {OUTPUT_PATH} 에 저장되었습니다.")