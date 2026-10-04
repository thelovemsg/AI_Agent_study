# AI_Agent_study

## 프로젝트 구조

```
AI_Agent/
├── .env                          # API 키 관리 (git에 올리지 않음)
├── README.md                     # 프로젝트 전체 안내
├── python_syntax.md              # Python 핵심 문법 정리 (Java/TS 대비)
├── java_annotation.md            # Java 어노테이션 원리 & 동작 시점
├── First/
│   ├── study1.py                 # OpenAI API 첫 번째 테스트 스크립트
│   └── README.md                 # 1차 학습 일지 (2026.10.03)
└── Second_Langchain/
    ├── study2.py                 # LangChain ChatOpenAI 기본 사용
    ├── 2_model_start.py          # temperature, invoke, stream, batch 테스트
    ├── 1_readme.md               # 환경 설정, SDK 비교, 토큰 정리
    └── 2_readme.md               # 엔지니어링 팁 & 실행 결과
```

## 학습 진행 현황

| 회차 | 날짜 | 주제 | 상세 |
|------|------|------|------|
| 1차 | 2026.10.03 | OpenAI API 기초 | [First/README.md](First/README.md) |
| 2차 | 2026.10.04 | LangChain 기초 | [1_readme.md](Second_Langchain/1_readme.md), [2_readme.md](Second_Langchain/2_readme.md) |
| - | 2026.10.04 | Python 문법 정리 | [python_syntax.md](python_syntax.md) |
| - | 2026.10.04 | Java 어노테이션 정리 | [java_annotation.md](java_annotation.md) |

## 환경 설정
- Python 가상환경(`.venv`) 사용
- 필요 패키지: `openai`, `python-dotenv`, `langchain`, `langchain-openai`
- API 키는 `.env` 파일에서 관리 (`OPEN_API_KEY`)
