# 실전 엔지니어링 팁 & 2_model_start.py

## 실전 엔지니어링 팁

### temperature (창의성 vs 정확성)

temperature = 모델의 **"자유도"**. 높을수록 다양한 단어를 선택하지만, 사실이 아닌 것도 지어낸다 (환각).

| temperature | 동작 | 비유 |
|-------------|------|------|
| 0.0 | 가장 확률 높은 답만 선택 | 교과서 답안 |
| 0.5 | 적당히 다양한 표현 | 숙련된 작가 |
| 1.0 | 창의적이지만 불확실 | 즉흥 연설 |

**목적별 권장값:**

| 작업 | 권장 temperature | 이유 |
|------|-----------------|------|
| 이력서 감수, 데이터 추출, 코드 생성, RAG | **0.0 ~ 0.1** | 정확성 우선. 환각 방지 |
| 마케팅 카피, 브레인스토밍, 소설, 페르소나 챗봇 | **0.7 ~ 1.0** | 창의성 우선 |

> **핵심: "정확해야 하면 낮추고, 창의적이어야 하면 올린다"**

```python
# temperature 설정 예시
model = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)  # 정확한 답변
model = ChatOpenAI(model="gpt-4o-mini", temperature=0.8)  # 창의적 답변
```

### timeout (장애 방지)

OpenAI 서버가 느려질 때, timeout이 없으면 우리 서버도 무한 대기 → 전체 장애로 이어질 수 있다.
빠르게 실패시키고 재시도하는 것이 안전하다.

```python
# 30초 안에 응답 없으면 에러 발생
model = ChatOpenAI(model="gpt-4o-mini", timeout=30)
```

| 상황 | timeout 없음 | timeout=30 |
|------|-------------|-----------|
| 서버 지연 | 무한 대기, 서비스 장애 | 30초 후 에러 → 재시도 가능 |
| 정상 응답 | 정상 | 정상 |

### max_tokens (비용 제한)

모델이 생성하는 **최대 출력 토큰 수**를 제한한다. 비용 방어막 역할.

```python
# 최대 500토큰까지만 응답 생성
model = ChatOpenAI(model="gpt-4o-mini", max_tokens=500)
```

- 악의적 프롬프트 인젝션이나 모델 무한 반복 오류로 인한 과금 폭탄 방지
- **주의**: 요약/번역처럼 긴 출력이 필요한 작업에서 너무 낮게 잡으면 응답이 잘린다

### stream() (스트리밍 출력)

`invoke()`는 전체 응답이 완성될 때까지 기다리지만, `stream()`은 **토큰이 생성되는 대로 실시간 출력**한다.
ChatGPT에서 글자가 하나씩 나오는 것과 같은 원리.

```python
# invoke() - 전체 응답 완성 후 한번에 받기
response = model.invoke("질문")
print(response.content)

# stream() - 실시간으로 토큰 하나씩 받기
for token in model.stream("질문"):
    print(token.content, end="", flush=True)
```

| 방식 | 사용자 경험 | 적합한 상황 |
|------|-----------|-----------|
| `invoke()` | 응답 완성까지 빈 화면 대기 | 백엔드 처리, 짧은 응답 |
| `stream()` | 글자가 실시간으로 나타남 | 챗봇 UI, 긴 응답 |

### batch() (일괄 처리)

여러 질문을 **한번에 병렬로** 처리한다. 하나씩 `invoke()` 하는 것보다 훨씬 빠르다.

```python
# 하나씩 호출 (느림)
r1 = model.invoke("질문1")
r2 = model.invoke("질문2")
r3 = model.invoke("질문3")

# batch로 한번에 (빠름)
responses = model.batch(["질문1", "질문2", "질문3"])
for r in responses:
    print(r.content)
```

| 방식 | 3개 질문 처리 시간 | 적합한 상황 |
|------|-------------------|-----------|
| `invoke()` × 3 | ~9초 (3초 × 3, 순차) | 단일 질문 |
| `batch()` | ~3초 (병렬 처리) | 대량 질문, 데이터 처리 |

`max_concurrency`로 동시 요청 수를 제한할 수 있다. API rate limit에 걸리지 않도록 조절하는 용도.

```python
# 최대 5개씩 동시 처리 (너무 많으면 rate limit 에러)
responses = model.batch(
    ["질문1", "질문2", "질문3", ...],
    config={"max_concurrency": 5}
)
```

### 모델 생성 시 옵션 종합 예시

```python
model = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=os.environ["OPEN_API_KEY"],
    temperature=0.1,    # 정확성 우선
    max_tokens=1000,    # 비용 제한
    timeout=30,         # 장애 방지
)
```

---

## 2_model_start.py 실행 결과

### 1. Temperature 비교

같은 질문 "사과의 매력을 한 문장으로 표현해줘."에 대해:

| temperature | 응답 |
|-------------|------|
| 0.0 | 사과는 아삭한 식감과 상큼한 단맛이 어우러져, 한 입 베어물면 자연의 신선함이 입안 가득 퍼지는 매력을 지니고 있다. |
| 1.0 | 사과는 아삭한 식감과 달콤한 맛이 어우러져 건강과 행복을 한입에 담아주는 자연의 선물입니다. |

- 0.0은 여러번 실행해도 **같은 답**이 나온다 (결정적)
- 1.0은 실행할 때마다 **다른 답**이 나온다 (확률적)

### 2. invoke() - 기본 호출

```
응답: 사과는 아삭한 식감과 상큼한 단맛이 어우러져...
토큰: input_tokens=20, output_tokens=45, total_tokens=65
```

- 전체 응답이 완성된 후 한번에 반환된다
- `response.usage_metadata`로 토큰 사용량 확인 가능

### 3. stream() - 실시간 스트리밍

```
앵무새가 말을 따라하는 이유는 주로 그들의 사회적 본능과 학습 능력 때문입니다...
```

- 토큰이 생성되는 대로 **한 글자씩 실시간 출력**됨
- `end=""`, `flush=True` 옵션으로 줄바꿈 없이 이어서 출력

### 4. batch() - 여러 질문 병렬 처리

3개 질문을 `max_concurrency=3`으로 동시 처리:

| 질문 | 답변 |
|------|------|
| 사과를 한 단어로 표현하면? | 사죄 |
| 바나나를 한 단어로 표현하면? | 노란색 |
| 포도를 한 단어로 표현하면? | 과일 |

- 3개 질문이 **병렬로 동시 실행**되어 순차 호출 대비 약 3배 빠름
- `config={"max_concurrency": N}`으로 동시 요청 수 제한 가능
