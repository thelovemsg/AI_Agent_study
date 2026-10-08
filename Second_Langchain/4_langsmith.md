# LangSmith (추적 · 평가 · 모니터링) & 4_langsmith_start.py

> 출처: 2-5) 랭스미스 · 학습일 2026.10.08

## 왜 쓰나

에이전트가 고도화될수록 내부 동작이 복잡해진다. 이때 **"어디서 어떤 입력으로 무엇이 실행됐는지"** 를 눈으로 확인할 수 있어야 디버깅과 품질 개선이 가능하다.

| 용도 | 할 수 있는 일 |
|---|---|
| **추적(Tracing)** | 모델 호출 순서, 입력/출력이 어떻게 흘렀는지 실행 경로 확인 |
| **평가(Evaluation)** | 특정 프롬프트/체인/에이전트가 테스트 데이터에서 잘 동작하는지 측정 |
| **모니터링** | 운영 중 토큰 사용량, 레이턴시, 에러율 확인 |

> "잘 만들었다"를 넘어 **"운영 가능한 수준으로 관리한다"** 는 관점의 도구.

**가장 큰 장점은 코드를 고치지 않는다는 것이다.** 환경변수만 켜면 기존 `invoke()` 호출이 전부 자동으로 기록된다. 로깅 코드를 심을 필요가 없다.

## 1) 계정과 API 키 발급

1. [smith.langchain.com](https://smith.langchain.com) 에서 계정 생성
2. 좌측 하단 **Settings → API Keys** 에서 키 발급
3. 발급한 키를 환경변수로 설정

발급된 키는 `lsv2_pt_...` 형태다. OpenAI 키와 마찬가지로 **생성 시 한 번만 보여주므로** 바로 복사해 둔다.

## 2) 환경변수 설정

### 환경변수 이름 (책과 다름)

책은 `LANGCHAIN_*` 를 쓰는데, 현재 권장되는 이름은 `LANGSMITH_*` 다. **둘 다 동작하지만** 새로 쓰는 코드는 뒤쪽을 쓰는 게 좋다.

| 책 (구) | 현재 권장 | 역할 |
|---|---|---|
| `LANGCHAIN_TRACING_V2` | `LANGSMITH_TRACING` | 추적 ON/OFF (`"true"`) |
| `LANGCHAIN_API_KEY` | `LANGSMITH_API_KEY` | LangSmith 키 |
| `LANGCHAIN_PROJECT` | `LANGSMITH_PROJECT` | 로그를 묶는 프로젝트 이름 |

`LANGSMITH_PROJECT` 는 **실행 로그를 묶는 단위**다. 프로젝트가 없으면 자동 생성된다.

### 우리 환경에서는 키를 코드에 적지 않는다

책은 이렇게 소개한다.

```python
# 책 방식 - 따라하지 말 것
os.environ["LANGCHAIN_API_KEY"] = "lsv2_pt_실제키..."
```

Colab 실습용이라 그렇지만, **git으로 관리하는 프로젝트에서는 절대 하면 안 된다.** 우리는 `.env`에 둔다.

```
# .env
OPEN_API_KEY=sk-...
LANGSMITH_API_KEY=lsv2_pt_...
```

```python
# 4_langsmith_start.py 방식
load_dotenv()                                  # .env에서 LANGSMITH_API_KEY를 읽어온다
os.environ["LANGSMITH_TRACING"] = "true"       # 키가 아닌 설정값만 코드에 둔다
os.environ["LANGSMITH_PROJECT"] = "AI_Agent_study"
```

### 설정은 모델 임포트보다 먼저

> 모델을 임포트/초기화하기 **전에** 설정을 먼저 잡아둬야 한다.

그래서 `4_langsmith_start.py`는 import 문이 위아래로 나뉘어 있다. 파일 맨 위에 모든 import를 모아두는 평소 습관과 다르다.

```python
from dotenv import load_dotenv      # 1. 먼저 .env 로드
import os
load_dotenv()

os.environ["LANGSMITH_TRACING"] = "true"   # 2. 추적 설정

from langchain.chat_models import init_chat_model   # 3. 그 다음 모델 임포트
```

### 패키지는 추가 설치가 필요 없다

`langsmith` 는 `langchain-core` 의 의존성이라 이미 깔려 있다. 확인:

```bash
pip show langsmith
```

## 3) init_chat_model

이 장에서 모델 생성 방식이 바뀐다.

```python
# 지금까지 (2~3차)
from langchain_openai import ChatOpenAI
model = ChatOpenAI(model="gpt-4o-mini", api_key=OPEN_API_KEY)

# 이번 장
from langchain.chat_models import init_chat_model
model = init_chat_model("gpt-4o-mini", model_provider="openai", api_key=OPEN_API_KEY)
```

| | `ChatOpenAI` | `init_chat_model` |
|---|---|---|
| provider | OpenAI 고정 | **문자열로 교체 가능** |
| 임포트 | provider별로 다름 | 하나로 통일 |
| 교체 비용 | 클래스와 임포트를 모두 수정 | 문자열 한 개 |

provider를 바꿔보려면 모델명만 교체하면 된다 (해당 패키지는 따로 설치 필요).

```python
model = init_chat_model("claude-sonnet-4-5")   # langchain-anthropic
model = init_chat_model("gemini-2.0-flash")    # langchain-google-genai
```

### 주의: `api_key`를 명시해야 한다

`init_chat_model`은 기본적으로 **`OPENAI_API_KEY`** 환경변수를 찾는다. 우리 `.env`의 이름은 `OPEN_API_KEY`(`I` 없음)라서 그냥 두면 키를 못 찾는다.

```python
model = init_chat_model(
    "gpt-4o-mini",
    model_provider="openai",
    api_key=OPEN_API_KEY,   # <- 이 줄이 없으면 인증 실패
)
```

> 참고: 책은 `gpt-5-nano`를 쓴다. 우리는 이전 학습과 조건을 맞추기 위해 `gpt-4o-mini`를 유지했다. 모델 문자열만 바꾸면 그대로 동작한다.

## 4) 대시보드에서 확인되는 것

실행 후 [smith.langchain.com](https://smith.langchain.com) → 프로젝트(`AI_Agent_study`) 로 이동.

| 항목 | 내용 |
|---|---|
| 입력 / 출력 | 실제로 모델에 들어간 **메시지 전체**와 응답 |
| 실행 시간 | 시작·종료 시각, 레이턴시 |
| 토큰 사용량 | 입력 / 출력 / 총합 |
| 상태 | 성공 / 실패 (에러는 스택트레이스까지) |

**메시지 전체가 보이는 게 특히 유용하다.** 3차 학습의 `trim_messages`가 의도대로 잘라냈는지, 시스템 메시지가 안 잘렸는지를 추측하지 않고 눈으로 확인할 수 있다.

## 5) 추적에 이름·태그 달기

호출이 쌓이면 대시보드에서 어느 게 무엇인지 구분이 안 된다. `config`로 메타데이터를 달면 검색·필터가 가능해진다.

```python
response = model.invoke(
    "질문",
    config={
        "run_name": "langsmith-intro",                  # 실행 이름
        "tags": ["lesson4", "smoke-test"],              # 필터용 태그
        "metadata": {"lesson": "2-5", "env": "local"},  # 임의 부가 정보
    },
)
```

실무에서는 `metadata`에 `user_id`, `resume_id`, `version` 같은 걸 넣어둔다. 특정 사용자의 문제를 재현할 때 그 사용자의 호출만 뽑아볼 수 있다.

## 6) `@traceable` — 내가 만든 함수도 추적

LLM 호출만 기록하면 **"전처리에서 뭘 잘못 넣었는지"** 는 안 보인다. 프롬프트 조립 함수에 `@traceable`을 붙이면 실행 경로에 함께 기록된다.

```python
from langsmith import traceable

@traceable(name="build_review_prompt")
def build_review_prompt(items): ...

@traceable(name="review_resume")
def review_resume(items):
    prompt = build_review_prompt(items)   # 중첩 호출은 트리 구조로 기록된다
    return model.invoke(prompt).content
```

대시보드에 이런 트리로 나타난다.

```
review_resume
├── build_review_prompt        ← 입력 items, 출력 messages 확인 가능
└── ChatOpenAI                 ← 실제 LLM 호출
```

[career_agent.md](../career_agent.md)의 `build_prompt()` 처럼 **상태를 조립해서 프롬프트에 꽂는 함수**가 생기면 여기에 붙이는 게 좋다. 완성도 평가, diff 렌더링, 제안 조회 중 어디서 잘못된 값이 들어갔는지 추적할 수 있다.

---

## 4_langsmith_start.py 구성

| 섹션 | 확인하는 것 |
|---|---|
| [0] 설정 | 추적 ON, 프로젝트 지정. 키 없으면 경고 후 추적만 끄고 진행 |
| [1] `init_chat_model` | 문자열로 모델 생성, 토큰 사용량 출력 |
| [2] run_name / tags | 대시보드에서 이름·태그로 필터되는지 |
| [3] 멀티턴 | 입력 메시지 전체가 trace에 남는지 |
| [4] `@traceable` | 내 함수가 트리 구조로 기록되는지 |

실행:

```bash
source .venv/Scripts/activate
python Second_Langchain/4_langsmith_start.py
```

`LANGSMITH_API_KEY`가 없으면 **추적만 끄고 스크립트는 정상 실행**된다. 키를 나중에 받아도 코드 수정 없이 `.env`에만 추가하면 된다.

## 다음 학습

- **평가(Evaluation)** — 데이터셋 만들고 `evaluate()`로 프롬프트 변경 전후 비교
- **3-3) Built-in 미들웨어** — 요약 전략
