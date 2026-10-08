# Memory (대화 맥락 유지) & 3_memory_start.py

> 출처: [2-4) Memory](https://wikidocs.net/331272) · 학습일 2026.10.08

## 핵심 한 줄

**LangChain의 '메모리'는 저장소가 아니다.** 지금까지 주고받은 메시지를 리스트에 누적해서 **매번 전체를 다시 보내는 것**이 전부다.

LLM API는 완전한 **stateless**다. `invoke()` 호출 하나하나가 독립적이고, 서버는 직전에 무슨 대화를 했는지 들고 있지 않다.

```python
model.invoke("저는 Jay라고 합니다.")       # 알려줘도
model.invoke("제 이름이 뭐라고 했죠?")      # 다음 호출은 모른다
```

> **Java/Spring에 비유하면**: HTTP가 stateless라서 세션이 필요한 것과 같은 구조다.
> 다만 LLM에는 `HttpSession` 같은 서버측 저장소가 **없어서**, 클라이언트가 대화 전체를 매 요청마다 직접 들고 가야 한다.

따라서 챗봇의 "기억력"은 저장소에서 나오는 게 아니라, **입력으로 다시 제공되는 과거 메시지 리스트**에서 나온다.
여기서 말하는 메모리는 장기 저장소가 아니라, 현재 대화의 앞뒤 흐름을 잡아주는 **실시간 단기 컨텍스트**에 가깝다.

## 메시지 3종

| 메시지 | 클래스 | role | 역할 |
|---|---|---|---|
| 시스템 메시지 | `SystemMessage` | `system` | 개발자가 미리 부여하는 역할·규칙 프롬프트. 사용자에게는 안 보인다 |
| 사용자 메시지 | `HumanMessage` | `human` | 사용자가 입력한 질문·지시 |
| AI 메시지 | `AIMessage` | `ai` | 모델이 생성한 답변 |

이 셋이 **발생한 순서대로 누적**되고, 모델은 이 전체 리스트를 읽어 다음 답변을 만든다.
그래서 사용자가 "제 이름이 뭐죠?" 같은 짧은 질문만 던져도 문맥에 맞는 답이 나온다.

### import 경로 주의 (내 환경 관련)

| 경로 | 동작하는 버전 |
|---|---|
| `from langchain.messages import ...` | **langchain 1.x 전용** (책에서 쓰는 경로) |
| `from langchain_core.messages import ...` | **0.3.x / 1.x 모두** |

우리 프로젝트는 `langchain_core` 경로를 쓴다. 버전에 관계없이 동작하고, 메시지 클래스의 실제 구현이 원래 `langchain-core` 패키지에 있기 때문이다. 책 코드를 그대로 복사하면 `ModuleNotFoundError`가 날 수 있으니 이 부분만 바꿔서 쓰면 된다.

## 방법 1) 메시지 객체 활용

```python
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

messages = [
    SystemMessage("당신은 친절한 조교입니다."),
    HumanMessage("안녕하세요. 저는 Jay라고 합니다."),
    AIMessage("안녕하세요 Jay님, 반갑습니다. 무엇을 도와드릴까요?"),
    HumanMessage("제가 방금 제 이름을 뭐라고 했죠?"),
]

response = model.invoke(messages)   # -> "Jay라고 하셨어요."
```

**`AIMessage`를 다시 넣어주는 게 핵심이다.** 모델의 과거 답변을 리스트에 안 넣으면 모델은 자기가 뭐라고 답했는지 모른다.

## 방법 2) 딕셔너리 활용

```python
messages = [
    {"role": "system", "content": "당신은 유능한 로켓 전문가입니다."},
    {"role": "human",  "content": "안녕하세요. 궁금한 게 있어요!"},
    {"role": "ai",     "content": "로켓 관련 무엇이든 물어보세요."},
    {"role": "human",  "content": "추진 방식 차이를 설명해 주세요"},
]

response = model.invoke(messages)   # 내부에서 알아서 변환해준다
```

| 방식 | 장점 | 적합한 상황 |
|---|---|---|
| 메시지 객체 | 타입이 명확해 IDE 자동완성·타입 체크가 된다 | 코드 안에서 직접 조립할 때 |
| 딕셔너리 | **직렬화·전송이 쉽다** (그대로 JSON) | DB에 대화 기록을 저장했다가 조회해 밀어넣을 때 |

## 멀티턴 대화 누적 패턴

실무에서 쓰는 구조는 결국 이 3줄의 반복이다.

```python
history = [SystemMessage("당신은 친절한 조교입니다.")]

history.append(HumanMessage(user_input))   # (1) 사용자 발화 누적
answer = model.invoke(history)             # (2) 리스트 '전체'를 전달
history.append(answer)                     # (3) 모델 답변도 누적  <- 빼먹기 쉬운 줄
```

턴이 쌓일수록 `response.usage_metadata['input_tokens']`가 계속 증가한다. **대화가 길어지면 입력 토큰이 선형으로 늘고, 비용도 같이 늘어난다.** 이게 다음 섹션의 출발점이다.

## 왜 끝없이 누적하면 안 되나

| 문제 | 내용 |
|---|---|
| **비용 및 지연 시간 증가** | 입력 토큰이 늘어날수록 호출 비용이 오르고 응답 속도가 느려진다 |
| **컨텍스트 윈도우 초과** | 모델이 한 번에 처리할 입력 한계를 넘으면 정보가 잘리거나 에러가 난다 |
| **어텐션 분산** | 초반 시스템 메시지의 핵심 규칙이 방대한 과거 대화에 밀려 지시 수행 능력이 떨어진다 |
| **할루시네이션 / 정보 충돌** | 오래된 정보와 최신 정보가 섞이면 모델이 임의로 결론을 낸다 |

> 실무의 메모리 관리란 대화를 저장하는 일이 아니라, **한정된 토큰 예산 안에서 모델에 넣을 핵심 정보를 선별하는 최적화 작업**이다.

## 메모리 관리 전략 5가지

| 전략 | 기준 | 장점 | 단점 | 이 프로젝트 |
|---|---|---|---|---|
| 1) 슬라이딩 윈도우 | 최근 N턴 | 구현이 직관적, 비용 예측 쉬움 | 초반 제약사항·이름을 잃어버린다 | 구현함 |
| 2) **토큰 예산 트리밍** | 토큰 수 | 비용 상한을 직접 통제 | 여전히 오래된 맥락은 손실 | 구현함 (**권장 기본값**) |
| 3) 요약 + 최근 유지 | 하이브리드 | 긴 대화의 흐름·결정사항 보존 | 요약에 추가 LLM 호출 비용 | 구현함 (3-3 미들웨어에서 정식 등장) |
| 4) 상태(State) 분리 | 구조화된 사실 | 일관성이 비약적으로 향상 | 추출 로직을 따로 만들어야 함 | LangGraph에서 |
| 5) 검색 기반 (RAG) | 연관성 | 방대한 기록에서 필요한 조각만 | 검색 인프라 필요 | 4장에서 |

### 1) 슬라이딩 윈도우

가장 최근 맥락만 중요할 때. **시스템 메시지는 반드시 고정**하고 나머지만 잘라낸다.

```python
def sliding_window(messages, n=4):
    system = [m for m in messages if isinstance(m, SystemMessage)]
    rest = [m for m in messages if not isinstance(m, SystemMessage)]
    return system + rest[-n:]      # 음수 인덱스 슬라이싱 = 뒤에서 n개
```

### 2) 토큰 예산 기반 트리밍 (권장)

턴 수보다 **실제 토큰 수**를 제한해야 할 때. `trim_messages`로 정교하게 통제한다.

```python
from langchain_core.messages.utils import trim_messages, count_tokens_approximately

trimmed = trim_messages(
    messages,
    strategy="last",                           # 오래된 것을 버리고 최근을 유지
    token_counter=count_tokens_approximately,  # 토큰 계산 함수
    max_tokens=2000,                           # 입력 토큰 상한
    include_system=True,                       # 시스템 메시지는 잘리지 않게 고정(핀)
    start_on="human",                          # 결과가 반드시 사람 질문으로 시작
    end_on=("human", "tool"),                  # 결과가 사람 질문으로 끝나도록 보장
)

response = model.invoke(trimmed)
```

| 옵션 | 왜 필요한가 |
|---|---|
| `include_system=True` | 역할 설정이 잘려나가면 페르소나가 무너진다 |
| `start_on="human"` | `AIMessage`로 시작하는 대화는 모델이 어색하게 받는다 |
| `end_on=("human","tool")` | 마지막이 AI 답변이면 모델이 답할 차례가 아니게 된다 |
| `count_tokens_approximately` | 실제 토크나이저보다 빠른 근사 계산. 매 턴 돌려도 부담 없다 |

### 3) 요약 + 최근 대화 유지 (하이브리드)

긴 대화에서 전체 흐름과 결정사항을 유지해야 할 때. 과거 대화를 LLM으로 **한 덩어리로 압축**한다.
실무 표준 구성은 **요약본 1개 + 최근 원문 N개**이고, **요약본은 시스템 메시지 쪽에 고정**한다(그래야 트리밍에 안 잘린다).

```python
hybrid = [
    SystemMessage(f"당신은 친절한 조교입니다.\n\n[이전 대화 요약]\n{summary}"),
    *recent_messages,       # 최근 원문 N개
    HumanMessage(user_input),
]
```

슬라이딩 윈도우에서 잃어버린 "사용자 이름"이 요약본에는 남아 있기 때문에, 같은 질문에 다시 답할 수 있게 된다.

---

## 3_memory_start.py 구성

| 섹션 | 확인하는 것 |
|---|---|
| [1] 메모리 없음 | `invoke()`가 독립 호출이라 이름을 기억하지 못함 |
| [2] 메시지 객체 | `AIMessage`를 넣으면 기억하는 것처럼 동작 |
| [3] 딕셔너리 | `role`/`content`로도 동일하게 동작 |
| [4] 멀티턴 누적 | 턴마다 `input_tokens`가 증가 (비용 누적) |
| [5] 슬라이딩 윈도우 | 토큰은 줄지만 초반 정보(이름) 손실 |
| [6] `trim_messages` | 토큰 상한 적용 후 남은 메시지 구성 출력 |
| [7] 요약 하이브리드 | 요약본에 이름이 남아 다시 기억함 |

실행:

```bash
source .venv/Scripts/activate
python Second_Langchain/3_memory_start.py
```

[5]와 [7]을 같은 질문("제 이름이 뭐였죠?")으로 맞춰뒀으니, **두 답변을 비교**하는 게 이 실습의 핵심이다.

## 다음 학습

- **3-3) Built-in 미들웨어** — 요약 전략을 LangChain이 제공하는 방식으로
- **LangGraph** — 전략 4) 상태(State) 분리
- **4장 RAG** — 전략 5) 검색 기반 장기 메모리
