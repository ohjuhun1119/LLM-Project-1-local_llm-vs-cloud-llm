'''mermaid
flowchart TD
    A[문제 정의] --> B[모델 요구사항 정의]
    B --> C[Use Case 선정]
    C --> D[후보 모델 리서치<br/>Gemma3 4B / Qwen3 4B]
    D --> E[실행 환경 준비<br/>Ollama 설치·모델 다운로드]
    E --> F[평가 질문·채점 기준 설계]
    F --> G[로컬 모델 비교 실험 실행]
    G --> H{두 모델 중<br/>필수 조건 통과?}
    H -->|둘 다 통과| I[선호 우선순위로<br/>1개 모델 선정]
    H -->|일부만 통과| J[통과한 모델 선정]
    I --> K[Cloud API 소규모 비교]
    J --> K
    K --> L{Local이 Cloud 대비<br/>충분한 성능인가?}
    L -->|Yes| M[Local 운영 권고]
    L -->|No| N[Cloud 또는 하이브리드 운영 권고]
    M --> O[최종 모델 선정 보고서 작성]
    N --> O
'''
