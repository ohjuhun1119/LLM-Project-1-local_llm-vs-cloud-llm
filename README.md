## 프로젝트 제목 : local LLM vs Cloud LLM 비교 프로젝트

로컬 LLM 2개를 ollama로 동일 조건에서 비교해 서비스 상황에 맞는 모델을 선정하고, Cloud API 모델과 소규모 비교를 통해 운영 방식을 검토하는 프로젝트입니다.


## 프로젝트 개요 
- **문제 정의**: [docs/00-problem-definition.md](docs/00-problem-definition.md)
- **모델 요구사항**: [docs/01-requirements.md](docs/01-requirements.md)
- **Use Case**: [docs/02-use-case.md](docs/02-use-case.md)
- **후보 모델**: Gemma 3 4B, Qwen 3 4B-instruct-2507-q4_K_M (Local) / Cloud API 1종
- **후보 모델 설정 이유 및 타 모델 비교**: [docs/03-candidate-model.md](docs/03-candidate-model.md)
- **flowchart**: [docs/04-flowchart.md](docs/04-flowchart.md)
- **평가 질문 및 채점 기준**:[docs/05-eval-questions.md](docs/05-eval-questions.md)


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


- ## 작업 순서

- [x] 문제 정의
- [x] 모델 요구사항 정의
- [x] Use Case 선정
- [x] 후보 모델 리서치
- [x] 평가 질문 설계
- [x] 실행 환경 준비
- [x] 로컬 모델 비교 실험
- [ ] Cloud API 소규모 비교
- [ ] 최종 모델 선정 및 보고서 작성