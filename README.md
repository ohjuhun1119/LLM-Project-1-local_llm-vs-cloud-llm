## 프로젝트 제목 : local LLM vs Cloud LLM 비교 프로젝트

로컬 LLM 2개를 ollama로 동일 조건에서 비교해 서비스 상황에 맞는 모델을 선정하고, Cloud API 모델과 소규모 비교를 통해 운영 방식을 검토하는 프로젝트입니다.

## 프로젝트 개요 
- **문제 정의**: [docs/00-problem-definition.md](docs/00-problem-definition.md)
- **모델 요구사항**: [docs/01-requirements.md](docs/01-requirements.md)
- **Use Case**: [docs/02-use-case.md](docs/02-use-case.md)
- **후보 모델**: Gemma 3 4B, Qwen 3 4B-instruct-2507-q4_K_M (Local) / Cloud API 1종
- **후보 모델 설정 이유 및 타 모델 비교**: [docs/03-candiate-model.md](docs/03-candidate-model.md)
- **flowchart**: [docs/04-flowchart.md](docs/04-flowchart.md)
- **평가 질문 및 채점 기준**:[docs/05-eval-questions.md](docs/05-eval-questions.md)

## 실행 방법

## 작업 순서

- [x] 문제 정의
- [x] 모델 요구사항 정의
- [x] Use Case 선정
- [x] 후보 모델 리서치
- [x] 평가 질문 설계
- [x] 실행 환경 준비
- [ ] 로컬 모델 비교 실험
- [ ] Cloud API 소규모 비교
- [ ] 최종 모델 선정 및 보고서 작성