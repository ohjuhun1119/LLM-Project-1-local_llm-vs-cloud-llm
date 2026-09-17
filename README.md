## 프로젝트 제목 : local LLM vs Cloud LLM 비교 프로젝트

로컬 LLM 2개를 ollama로 동일 조건에서 비교해 서비스 상황에 맞는 모델을 선정하고, Cloud API 모델과 소규모 비교를 통해 운영 방식을 검토하는 프로젝트입니다.


## 프로젝트 개요 
- **문제 정의**: [docs/00-problem-definition.md](docs/00-problem-definition.md)
- **모델 요구사항**: [docs/01-requirements.md](docs/01-requirements.md)
- **Use Case**: [docs/02-use-case.md](docs/02-use-case.md)
- **후보 모델**: Gemma 3 4B, Qwen 3 4B-instruct-2507-q4_K_M (Local) / Cloud API (gpt-5.6-luna)
- **후보 모델 설정 이유 및 타 모델 비교**: [docs/03-candidate-model.md](docs/03-candidate-model.md)
- **flowchart**: [docs/04-flowchart.md](docs/04-flowchart.md)
- **평가 질문 및 채점 기준**:[docs/05-eval-questions.md](docs/05-eval-questions.md)
- **Qwen, Gemma 로컬 실행 응답**:[docs/06-model-response.md](docs/06-model-response.md)
- **모델 별 평가 및 종합 비교**: [docs/07-model-comparison.md](docs/07-model-comparison.md)
- **local, cloud 비교표 작성**:[docs/08-local-vs-cloud.md](docs/08-local-vs-cloud.md)

## 개발 환경 설정

### Python 라이브러리 설치

```bash
pip install ollama requests
```

### VS Code 파이썬 인터프리터 설정

이 프로젝트는 Anaconda(conda) 환경을 사용합니다. `import ollama`에 
노란 경고 줄이 뜨는 경우, VS Code가 다른 파이썬 환경을 보고 있는 것이니 
아래처럼 인터프리터를 맞춰주세요.

1. `Cmd + Shift + P` → `Python: Select Interpreter` 검색
2. Anaconda 환경(`base` 또는 `conda`가 포함된 항목) 선택
3. 하단 상태바에 선택된 파이썬 환경이 표시되는지 확인

이 설정은 `.vscode/settings.json`에 자동 저장되며, 프로젝트에 포함되어 
git으로 함께 관리됩니다.

**`.vscode/settings.json`**
```json
{
    "editor.suggest.selectionMode": "never",
    "python-envs.defaultEnvManager": "ms-python.python:conda",
    "python-envs.defaultPackageManager": "ms-python.python:conda"
}
```

### Ollama 서버 확인

스크립트 실행 전, Ollama 앱이 켜져 있고 서버가 응답하는지 확인합니다.

```bash
ollama -v        # 버전 확인
ollama list       # 설치된 모델 목록 확인
```


## 폴더 구조

```
.
├── docs/                          # 단계별 문서
│   ├── 00-problem-definition.md
│   ├── 01-requirements.md
│   ├── 02-use-case.md
│   ├── 03-candidate-model.md
│   ├── 04-flowchart.md
│   ├── 05-eval-questions.md
│   ├── 06-model-response.md
│   ├── 07-model-comparison.md
│   └── 08-local-vs-cloud.md
├── src/                           # 실험 실행 스크립트
│   ├── 01_check_environment.py    # STEP 3: 실행 환경 확인
│   ├── 02_run_eval_questions.py   # STEP 6: 로컬 모델 비교 실험
│   └── 03_cloud_eval_questions.py # STEP 7: Cloud API 비교
├── results/                       # 실험 결과 (JSON)
│   ├── environment_check_log.json
│   ├── local_eval_log.json
│   └── luna_eval_log.json
└── README.md
```


## 실행 방법
### 1. ollama 모델 다운로드
```bash
ollama pull gemma3:4b
ollama pull qwen3:4b-instruct-2507-q4_K_M
```

### 2. Python 라이브러리 설치
```bash
pip install ollama
```

### 3. 실행 환경 확인

두 후보 모델에 동일한 질문(Q1)을 보내고, 기본 응답 / ollama 버전 / 장비 정보 / 생성 설정 / 원본 응답을 'results/environment_check_log.json'에 기록합니다.

```bash
python src/01_check_environment.py
```

**확인사항**:
- 두 모델이 정상적으로 응답하는지
- results/environment_check_log.json에 아래 정보가 모두 기록되는지
    - 'ollama_version' : 설치된 ollama 버전
    - 'device_info' : 설치된 ollama 버전
    - 'generation_settings' : temperature, num_predict 생성 설정
    - 'results' : 각 모델의 응답 텍스트 및 원본 응답


### 4. 로컬 모델 비교 실험

10개 질문(Q1~Q10)을 두 모델에 각각 2회씩(워밍업 1회 별도) 실행하고,
응답 텍스트뿐 아니라 응답 시간·토큰 생성 속도·VRAM 사용량·모델 상세 정보(digest, 
quantization_level, context_length)까지 `results/local_eval_log.json`에 기록합니다.

```bash
python src/02_run_eval_questions.py
```

**확인사항**:
- 모델당 20회(10문항 × 2회)씩 정상적으로 응답하는지
- `results/local_eval_log.json`에 아래 정보가 모두 기록되는지
    - `warmup`: 워밍업 결과 (본 집계와 별도 기록)
    - `results`: 질문별·회차별 응답, 성능 지표(elapsed_sec, tokens_per_sec, vram)
    - `model_details`: 모델별 digest, quantization_level, context_length

### 5. Cloud API(Luna) 소규모 비교

STEP 5에서 미리 선정한 공통 질문 5개(Q1, Q3, Q5, Q6, Q9)를 Cloud API(`gpt-5.6-luna`)에
각 1회씩 실행하고, 응답·성공/오류 상태·입력출력 토큰·응답 시간·예상 비용을
`results/luna_eval_log.json`에 기록합니다.

```bash
python src/03_cloud_eval_questions.py
```

실행 시 OpenAI API 키를 입력하라는 프롬프트가 뜹니다 (화면에 표시되지 않으며, 코드·로그 어디에도 저장되지 않습니다).

**확인사항**:
- 5개 질문 모두 정상 응답하는지 (`성공 비율` 필드로 확인)
- 비용은 **추정치**이며, [OpenAI 사용량 대시보드](https://platform.openai.com/usage)의
  실제 청구 내역과 반드시 대조해야 합니다

- ## 작업 순서

- [x] 문제 정의
- [x] 모델 요구사항 정의
- [x] Use Case 선정
- [x] 후보 모델 리서치
- [x] 평가 질문 설계
- [x] 실행 환경 준비
- [x] 로컬 모델 비교 실험
- [x] Cloud API 소규모 비교
- [ ] 최종 모델 선정 및 보고서 작성