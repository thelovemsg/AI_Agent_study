# Second - LangChain

## 환경 설정

### 패키지 설치

가상환경 활성화 후 설치:

```bash
python -m pip install langchain langchain-openai
```

### .env 설정

프로젝트 루트(`AI_Agent/`)에 `.env` 파일 생성:

```
OPEN_API_KEY=sk-proj-xxxxxxxx
```

## study2.py - LangChain으로 OpenAI 모델 사용하기

`langchain_openai`의 `ChatOpenAI`를 사용하여 OpenAI 모델을 호출하는 기본 예제.

### 핵심 코드

```python
from langchain_openai import ChatOpenAI

model = ChatOpenAI(model="gpt-4o-mini", api_key=os.environ["OPEN_API_KEY"])
response = model.invoke("질문 내용")
print(response.content)
```

### OpenAI SDK vs ChatOpenAI (LangChain) 차이

`OpenAI`는 OpenAI 공식 SDK이고, `ChatOpenAI`는 LangChain이 OpenAI를 감싼 래퍼(wrapper)다.
내부적으로 같은 OpenAI 서버에 요청을 보내지만, LangChain을 통해 쓰면 체인/에이전트/RAG 등 확장이 쉬워진다.

| 항목 | OpenAI SDK (study1.py) | LangChain (study2.py) |
|------|----------------------|----------------------|
| 패키지 | `openai` | `langchain-openai` |
| 클라이언트 | `OpenAI()` | `ChatOpenAI()` |
| 호출 방식 | `client.responses.create()` | `model.invoke()` |
| 응답 접근 | `response.output_text` | `response.content` |
| 비유 | 엔진 직접 조작 | 자동차에 탑승 (엔진은 같음) |

### LangChain이 지원하는 다른 모델들

LangChain의 핵심 장점: **모델만 바꾸면 나머지 코드(`invoke()`, `stream()`, `batch()`)는 동일하게 사용 가능**

| 모델 | 패키지 설치 | 클래스 | 코드 예시 |
|------|-----------|--------|----------|
| OpenAI | `pip install langchain-openai` | `ChatOpenAI` | `ChatOpenAI(model="gpt-4o-mini")` |
| Claude (Anthropic) | `pip install langchain-anthropic` | `ChatAnthropic` | `ChatAnthropic(model="claude-sonnet-4-20250514")` |
| Gemini (Google) | `pip install langchain-google-genai` | `ChatGoogleGenerativeAI` | `ChatGoogleGenerativeAI(model="gemini-pro")` |
| Ollama (로컬) | `pip install langchain-ollama` | `ChatOllama` | `ChatOllama(model="llama3")` |

```python
# 예시: 모델만 바꾸면 코드 구조는 동일
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

model = ChatOpenAI(model="gpt-4o-mini")          # OpenAI
model = ChatAnthropic(model="claude-sonnet-4-20250514")  # Claude
model = ChatGoogleGenerativeAI(model="gemini-pro")  # Gemini

# 어떤 모델이든 동일한 방식으로 호출
response = model.invoke("질문")
print(response.content)
```

### 실행

```bash
.venv/Scripts/python Second_Langchain/study2.py
```

### 실행 결과

`response`를 그대로 출력하면 메타데이터가 전부 노출된다:

```
content='앵무새의 털 색상이 다양한 이유는...' additional_kwargs={...} response_metadata={...} usage_metadata={...}
```

`response.content`로 접근하면 응답 텍스트만 깔끔하게 출력된다:

```
앵무새의 털 색상이 다양한 이유는 주로 진화, 생태적 역할, 그리고 유전적 다형성 때문입니다.
1. 진화적 적응
2. 짝짓기와 성적 선호
3. 유전자 다양성
4. 사회적 신호
```

### response 객체에 포함된 주요 정보

| 필드 | 설명 |
|------|------|
| `response.content` | 실제 응답 텍스트 |
| `response.response_metadata` | 모델명, 종료 사유, 토큰 사용량 등 |
| `response.usage_metadata` | 토큰 사용량 요약 |

### 토큰 사용량 확인

실행 결과에서 토큰 정보를 확인할 수 있다:

```python
response.usage_metadata
# {'input_tokens': 23, 'output_tokens': 335, 'total_tokens': 358}
```

| 항목 | 값 | 설명 |
|------|---|------|
| input_tokens | 23 | 질문에 사용된 토큰 |
| output_tokens | 335 | 응답에 사용된 토큰 |
| total_tokens | 358 | 총 사용 토큰 |

### 토큰 주의점

- **토큰 = 과금 단위**: API 호출 시 input + output 토큰 합계로 비용이 청구된다.
- **한글은 토큰 효율이 낮다**: 영어는 1단어 ≈ 1토큰이지만, 한글은 1글자에 2~3토큰을 소비할 수 있다. 같은 의미라도 한글이 더 많은 토큰을 쓴다.
- **모델마다 최대 토큰 제한이 있다**: `gpt-4o-mini`는 입력 128K, 출력 16K 토큰 제한. 초과 시 응답이 잘리거나 에러가 발생한다.
- **긴 대화는 토큰이 누적된다**: LangChain에서 대화 기록을 유지하면 매 호출마다 이전 대화 전체가 input_tokens에 포함되어 비용이 급증한다.
- **비용 절감 팁**: 불필요한 시스템 프롬프트 줄이기, 대화 기록 요약하기, 저렴한 모델(`gpt-4o-mini`) 활용하기.