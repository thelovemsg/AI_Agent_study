# 에이전트 기초 (3-1) & 1_agent_*.py

> 출처: 3-1) 에이전트 기초 · 학습일 2026.10.08

## 핵심 개념

에이전트의 가치는 유창한 문장 생성이 아니라 **실행력(Action)** 에 있다. 도구(Tool)를 호출해 외부 데이터를 가져오고, 그 결과를 바탕으로 답변을 만든다.

## 1) 왜 Tool이 필요한가

LLM은 **학습 시점 이전의 지식만** 가지고 있다. 실시간 날씨, 주가, 사내 DB 같은 건 모른다. Tool이 이 약점을 메운다 — 모델이 스스로 "이건 내 지식으론 부족하니 도구를 쓰자"고 판단하고 호출한다.

## 2) Tool 구현 방법 — `@tool` 데코레이터

모델이 도구를 **언제, 어떻게** 쓸지 판단하려면 세 가지가 필요하다.

| 요소 | 역할 |
|---|---|
| **함수 이름** | 도구의 직관적인 명칭 |
| **타입 힌트** | 입출력 타입 (모델이 인자를 조립하는 근거) |
| **독스트링** | 언제 쓰이고 어떤 역할인지 (모델이 선택하는 근거) |

```python
from langchain.tools import tool

@tool
def get_weather(location: str) -> str:
    """특정 지역의 날씨 정보를 제공합니다."""
    return f"{location}의 날씨는 맑고, 영하 2도입니다"
```

> 이름이나 설명이 모호하면 엉뚱한 도구를 고르거나, 도구 쓰기를 포기하고 자기 머릿속 지식으로 대충 답변해버린다.

## 3) 실습 1: 날씨 에이전트 (`1_agent_basic.py`)

### 에이전트 생성

```python
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

model = init_chat_model("gpt-4o-mini", model_provider="openai", api_key=OPEN_API_KEY)
agent = create_agent(model, tools=[get_weather])
```

- `create_agent`는 **모델 + 도구**를 결합해 에이전트 객체를 만든다.
- 내부적으로 LangGraph의 `langgraph-prebuilt`를 감싸는 wrapper다.

### 실행

```python
result = agent.invoke({
    "messages": [{"role": "user", "content": "서울 날씨 어때요?"}]
})
print(result["messages"][-1].content)
```

`invoke()`에 `"messages"` 키로 대화 리스트를 넘긴다 (`"message"` 아님 — s 빠뜨리면 빈 배열 에러).

### 실행 흐름 (messages 안에 기록되는 것)

```
HumanMessage("서울 날씨 어때요?")
  ↓
AIMessage(content='', tool_calls=[{name: 'get_weather', args: {location: '서울'}}])
  ↓  ← 모델이 직접 답하지 않고, 도구 호출 계획만 남김
ToolMessage(content='서울의 날씨는 맑고, 영하 2도입니다')
  ↓  ← 런타임이 실제 함수를 실행한 결과
AIMessage("현재 서울은 맑고 기온은 영하 2도예요...")
       ← ToolMessage를 읽고 최종 답변 생성
```

1. **계획 수립 (tool_calls)** — 모델이 "이 도구를 이렇게 실행해 줘"라는 계획을 AIMessage에 남김 (content는 비어있음)
2. **실제 실행 (ToolMessage)** — 런타임이 파이썬 함수를 실행하고 결과를 ToolMessage에 담음
3. **최종 답변** — 모델이 ToolMessage를 읽고 자연어 답변 완성

> Tool 호출 여부, 어떤 Tool인지, 인자 값 — 전부 **언어 모델이** 결정한다.

## 4) 실습 2: 시스템 프롬프트 (`1_agent_prompt_basic.py`)

### 문제: 도구를 안 쓰고 멋대로 답하는 모델

사칙연산 도구(add, multiply, divide)를 줘도, 간단한 계산은 **도구 없이 자기 머리로** 답하거나, 순서를 무시하고 병렬 호출해서 엉뚱한 인자를 넣는다.

시스템 프롬프트 없이 `42 + 3 * 23`을 물으면:

```
tool_calls=[
    multiply(3, 23),     # ← 맞음
    add(42, 0),          # ← multiply 결과를 안 기다리고 b=0을 넣어버림
]
```

불필요한 호출 1회 낭비 후 재호출해서 겨우 맞춤.

### 해결: 시스템 프롬프트로 통제

```python
agent = create_agent(
    model,
    tools,
    system_prompt="당신은 유능한 수학 선생님입니다. 추측하지 말고, 계산 시 모든 단계에서 tool들을 이용하시오."
)
```

→ 모델이 multiply 결과를 기다린 뒤 add를 순서대로 호출. 정확히 2회만 호출.

## 5) 실습 3: 외부 API 활용 (`1_agent_api.py`)

### 실무 Tool 작성 3대 원칙

| 원칙 | 내용 |
|---|---|
| **보안** | API 키를 코드에 하드코딩하지 않는다. `os.getenv`로 환경변수에서 주입 |
| **토큰 다이어트** | API 응답 전체를 모델에 던지지 않는다. 필요한 필드만 슬라이싱 |
| **우아한 실패** | 에러를 문자열로 반환해 모델이 "현재 조회 불가"라고 자연스럽게 대응 |

### 알라딘 베스트셀러 도구

```python
@tool
def fetch_aladin_bestseller_top10() -> Union[List[Dict[str, Any]], str]:
    """현재 시점의 알라딘 베스트셀러 Top 10 도서 목록을 조회하여 반환한다."""
    try:
        ttb_key = require_env("ALADIN_TTB_KEY")
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json().get("item", [])[:10]    # 토큰 다이어트
    except Exception as e:
        return f"API 호출 중 오류 발생. 원인: {str(e)}"  # 우아한 실패
```

에러가 나도 프로그램이 죽지 않고, 모델이 에러 메시지를 읽어 "현재 네트워크 오류로 조회 불가합니다" 같은 답변을 만들어낸다.

## 주의사항

### `init_chat_model`에 `api_key` 필수

`.env`의 키 이름이 `OPEN_API_KEY`(`I` 없음)라서 `init_chat_model`이 기본으로 찾는 `OPENAI_API_KEY`를 못 찾는다. 반드시 명시:

```python
model = init_chat_model("gpt-4o-mini", model_provider="openai", api_key=OPEN_API_KEY)
```

### `"messages"` 오타 주의

`invoke({"message": ...})` → s 빠지면 빈 배열 에러. 반드시 `"messages"`.

---

## 파일 구성

| 파일 | 내용 |
|---|---|
| `1_agent_basic.py` | Tool 정의, 에이전트 생성, 날씨 조회, 실행 흐름 확인 |
| `1_agent_prompt_basic.py` | 사칙연산 도구 + 시스템 프롬프트로 도구 사용 강제 |
| `1_agent_api.py` | 외부 API(알라딘) 호출 도구, 실무 3대 원칙 적용 |

실행:

```bash
source .venv/Scripts/activate
python 3rd_Langchain_agent_basic/1_agent_basic.py
python 3rd_Langchain_agent_basic/1_agent_prompt_basic.py
python 3rd_Langchain_agent_basic/1_agent_api.py
```
