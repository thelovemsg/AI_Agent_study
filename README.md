# AI_Agent_study

> **새 PC나 새로 clone한 폴더에서 실행하려면 [SETUP.md](SETUP.md)를 먼저 보세요.**
> `.venv/`와 `.env`는 git에 올라가지 않으므로, 가상환경 생성과 API 키 설정을 직접 해야 합니다.

```bash
python -m venv .venv                  # 최초 1회
source .venv/Scripts/activate         # 매번 (Git Bash 기준)
pip install openai python-dotenv langchain langchain-openai
```

## 프로젝트 구조

```
AI_Agent/
├── .env                          # API 키 관리 (git에 올리지 않음)
├── README.md                     # 프로젝트 전체 안내
├── SETUP.md                      # 초기 세팅 가이드 (새 환경에서 먼저 볼 문서)
├── career_agent.md               # 이력서 사서 서비스 설계 (DB 스키마 · 렌더링)
├── python_syntax.md              # Python 핵심 문법 정리 (Java/TS 대비)
├── java_annotation.md            # Java 어노테이션 원리 & 동작 시점
├── First/
│   ├── study1.py                 # OpenAI API 첫 번째 테스트 스크립트
│   └── README.md                 # 1차 학습 일지 (2026.10.03)
└── Second_Langchain/
    ├── 1_langchain_start.py      # LangChain ChatOpenAI 기본 사용
    ├── 1_readme.md               # 환경 설정, SDK 비교, 토큰 정리
    ├── 2_model_start.py          # temperature, invoke, stream, batch 테스트
    ├── 2_readme.md               # 엔지니어링 팁 & 실행 결과
    ├── 3_structured_response.py  # 구조화된 출력 (Pydantic, JSON Schema, frozen)
    ├── 3_readme.md               # 구조화된 출력, Pydantic 개념, 던더, model_config
    ├── 3_memory_start.py         # 메시지 누적, 슬라이딩 윈도우, trim_messages
    ├── 3_memory.md               # Memory (대화 맥락 유지) & 관리 전략 5가지
    ├── 4_langsmith_start.py      # LangSmith 추적, init_chat_model, @traceable
    └── 4_langsmith.md            # LangSmith (추적 · 평가 · 모니터링)
```

## 학습 진행 현황

| 회차 | 날짜 | 주제 | 상세 |
|------|------|------|------|
| 1차 | 2026.10.03 | OpenAI API 기초 | [First/README.md](First/README.md) |
| 2차 | 2026.10.04 | LangChain 기초 | [1_readme.md](Second_Langchain/1_readme.md), [2_readme.md](Second_Langchain/2_readme.md) |
| 3차 | 2026.10.05 | 구조화된 출력 (Structured Output) | [3_readme.md](Second_Langchain/3_readme.md) |
| 4차 | 2026.10.08 | Memory (대화 맥락 유지) | [3_memory.md](Second_Langchain/3_memory.md) |
| 5차 | 2026.10.08 | LangSmith (추적 · 모니터링) | [4_langsmith.md](Second_Langchain/4_langsmith.md) |
| - | 2026.10.04 | Python 문법 정리 | [python_syntax.md](python_syntax.md) |
| - | 2026.10.04 | Java 어노테이션 정리 | [java_annotation.md](java_annotation.md) |

## 설계 메모

학습 내용을 실제 서비스에 적용하기 위한 설계 정리.

| 문서 | 내용 |
|------|------|
| [career_agent.md](career_agent.md) | 이력서 사서 — 상태 분리 설계, DB 스키마, 제안 상태 관리, 이력서 렌더링 |

## 환경 설정

상세한 절차와 문제 해결은 [SETUP.md](SETUP.md) 참고.

- Python 가상환경(`.venv`) 사용
- 필요 패키지: `openai`, `python-dotenv`, `langchain`, `langchain-openai`
- API 키는 `.env` 파일에서 관리 (`OPEN_API_KEY`)
