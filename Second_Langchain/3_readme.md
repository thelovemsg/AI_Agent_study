# 구조화된 출력 (Structured Output) & 3_structured_response.py

## 왜 구조화된 출력이 필요한가?

LLM의 응답이 자유로운 텍스트로 돌아오면, 후속 처리(DB 저장, API 호출, 알림 발송)가 **불가능에 가까워진다.**
구조화된 출력은 모델의 답변을 **미리 약속한 데이터 형태(JSON 등)**로 받아내는 기법이다.

| 상황 | 비구조화 | 구조화 |
|------|---------|-------|
| 응답 형태 | "인셉션은 2010년 개봉한..." (자유 텍스트) | `{"title": "인셉션", "year": 2010, ...}` |
| 후속 처리 | 정규표현식 파싱 필요, 불안정 | 즉시 사용 가능, 안정적 |
| 시스템 연동 | 사람이 읽고 판단 | 자동화 파이프라인 연결 |

## 데이터 스키마(Data Schema)란?

데이터의 **구조, 타입, 제약 조건**을 명시한 설계도.

모델에게 스키마를 제공하는 것은 **"이 필드명과 타입을 반드시 준수하라"는 엄격한 계약**을 맺는 것과 같다.
스키마가 정교할수록 환각(Hallucination)이 줄어들고 시스템 안정성이 올라간다.

---

## 방법 1: Pydantic (추천)

파이썬 환경에서 **압도적으로 추천**하는 방식. 클래스 형태로 구조를 잡아 코드가 깔끔하고 IDE 자동완성을 100% 활용할 수 있다.

### 스키마 정의

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal

class Movie(BaseModel):
    """상세한 영화 정보."""
    title: str = Field(description="영화의 제목 (예: 인셉션)")
    year: Optional[int] = Field(default=None, description="개봉 연도. 정보를 알 수 없다면 None.")
    genre: Literal["액션", "로맨스", "SF", "코미디", "기타"] = Field(description="영화의 장르")
    director: str = Field(description="영화 감독 이름")
    rating: float = Field(description="영화 평점 (10점 만점 기준)")
```

### 핵심 설계 포인트

| 기법 | 적용 필드 | 효과 |
|------|----------|------|
| **타입 강제** (`str`, `float`) | title, director, rating | 문자열/숫자 타입 보장 |
| **Optional** | year | 모르면 None 반환. 할루시네이션 방지용 도망갈 구멍 |
| **Literal** (선택지 제한) | genre | 5가지 카테고리 안에서만 답하도록 강제 |
| **Field(description=...)** | 전체 | LLM이 읽는 프롬프트. 예시/제약 조건을 구체적으로 적으면 정확도 상승 |

> **Field의 description은 단순 주석이 아니다. LLM이 읽고 판단하는 프롬프트다.**

### 호출 및 결과

```python
model_with_structure = model.with_structured_output(Movie)
response = model_with_structure.invoke("영화 인셉션에 대해 설명해 주세요")

print(response.title)   # '인셉션'     (str)
print(response.rating)  # 8.8          (float)
print(response.genre)   # 'SF'         (Literal)
```

- `response.title`처럼 **점(.)으로 즉시 접근** 가능
- 평점은 **연산 가능한 float**으로 자동 타입 캐스팅
- 정규표현식 파싱 불필요

---

## Pydantic 핵심 개념 정리 (Java 대비)

### BaseModel = 데이터 클래스의 부모

`class Movie(BaseModel)`은 Java의 `extends`와 동일한 상속 문법이다.

```python
class Movie(BaseModel):    # Python: BaseModel 상속
```
```java
public record Movie(...) {}  // Java: record (불변 DTO)
```

BaseModel을 상속하면 자동으로 생기는 것:
- 생성자: `Movie(title="인셉션", year=2010, ...)`
- getter: `movie.title` (점으로 접근)
- `model_dump()`: dict로 변환 (Java의 ObjectMapper)
- `model_dump_json()`: JSON 문자열로 변환
- 타입 검증: 잘못된 타입 넣으면 에러 (Bean Validation)

### Field = 필드 레벨 어노테이션

| Field 옵션 | Java 대응 | 예시 |
|-----------|----------|------|
| `description="..."` | `@Schema(description="...")` | LLM이 읽는 프롬프트 |
| `default=None` | 필드 초기화 `= null` | 기본값 지정 |
| `ge=0, le=10` | `@Min(0) @Max(10)` | 숫자 범위 제한 |
| `min_length=1` | `@Size(min=1)` | 문자열 길이 제한 |

### Optional, Literal = 타입 힌트

| Python | Java 대응 | 용도 |
|--------|----------|------|
| `Optional[int]` | `@Nullable Integer` | None 허용 |
| `Literal["A","B","C"]` | `enum { A, B, C }` | 값 선택지 제한 |

### frozen = setter 차단 (불변 객체)

Java에서 `@Data` 대신 `record`나 `@Value`(Lombok)로 불변 객체를 만드는 것처럼,
Pydantic에서는 `model_config = {"frozen": True}`로 setter를 막는다.

```python
class ImmutableMovie(BaseModel):
    model_config = {"frozen": True}   # 이 한 줄이면 setter 차단

    title: str = Field(description="영화의 제목")
    director: str = Field(description="영화 감독 이름")
```

```python
movie = ImmutableMovie(title="인셉션", director="놀란")
movie.title = "변경"  # ValidationError! setter 차단됨
```

| 설정 | 동작 | Java 대응 |
|------|------|----------|
| 기본 (frozen 없음) | setter 가능 | `@Data` (getter + setter) |
| `frozen=True` | setter 차단, 읽기만 가능 | `record` / `@Value` (불변) |

> **실무 권장**: 에이전트 응답 스키마처럼 생성 후 변경할 이유가 없는 데이터는 `frozen=True`를 쓰는 게 안전하다.

---

## 방법 2: JSON Schema

스키마를 딕셔너리로 정의하는 방식. **언어 중립적**이라 타 언어와 스키마 공유 시 유용.

### 스키마 정의

```python
json_schema = {
    "title": "Movie",
    "description": "A movie with details",
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "The title of the movie"},
        "year": {"type": "integer", "description": "The year the movie was released"},
        "director": {"type": "string", "description": "The director of the movie"},
        "rating": {"type": "number", "description": "The movie's rating out of 10"},
    },
    "required": ["title", "director", "rating"]  # year는 필수 아님 (Optional과 동일)
}
```

### 호출 및 결과

```python
model_with_structure = model.with_structured_output(json_schema)
response = model_with_structure.invoke("영화 인터스텔라에 대해서 소개해 주세요")

print(response['title'])     # '인터스텔라'
print(response['director'])  # '크리스토퍼 놀란'
```

- 결과가 **딕셔너리(dict)**로 반환됨
- `response['title']`처럼 키로 접근

> **주의**: JSON Schema의 키값은 **영문, 숫자, 언더스코어** 중심으로 작성하는 것이 안전하다.

---

## 두 방식 비교

| 항목 | Pydantic | JSON Schema |
|------|----------|-------------|
| 반환 타입 | `Movie` 객체 | `dict` 딕셔너리 |
| 접근 방식 | `response.title` | `response['title']` |
| IDE 자동완성 | O | X |
| 유효성 검사 | 내장 (타입 자동 검증) | 별도 구현 필요 |
| 언어 중립성 | Python 전용 | 모든 언어에서 사용 가능 |
| 추천 상황 | **Python 에이전트 개발 (기본값)** | 외부 시스템과 스키마 공유, 동적 스키마 로딩 |

---

## Python 언더바(`_`) 규칙 & 던더(dunder)

### `type()`과 `__name__`

```python
type("hello")            # <class 'str'>       ← Java의 .getClass()
type("hello").__name__   # 'str'               ← Java의 .getClass().getSimpleName()
type(response).__name__  # 'Movie'
```

### 언더바 네이밍 규칙

| 형태 | 이름 | 의미 | Java 대응 |
|------|------|------|----------|
| `__name__` | 던더(dunder) | Python이 예약한 특수 속성/메서드 | `toString`, `equals` 등 |
| `__init__` | 던더 | 생성자 | `constructor` |
| `__str__` | 던더 | 문자열 표현 | `toString()` |
| `_변수` | 싱글 언더바 | 관례적 private (접근은 가능) | `private` (강제 아님) |
| `__변수` | 더블 언더바 | 네임 맹글링 (진짜 숨김) | `private` |

> **던더(dunder)** = **D**ouble **UNDER**score. 양쪽에 언더바 2개씩(`__xxx__`) 붙은 것.

### 던더를 직접 만들어도 되나?

**만들 수는 있지만 하면 안 된다.** `__xxx__`는 Python이 예약한 네이밍이라 현재/미래 내장 기능과 충돌 위험이 있다.

대신 Python이 정해둔 던더를 **오버라이드(재정의)**하는 건 자주 한다:

```python
class Movie:
    def __str__(self):       # Java의 toString() 오버라이드
        return f"영화: {self.title}"

    def __eq__(self, other):  # Java의 equals() 오버라이드
        return self.title == other.title
```

| 던더 메서드 | Java 대응 | 용도 |
|------------|----------|------|
| `__init__` | 생성자 | 객체 초기화 |
| `__str__` | `toString()` | `print()` 시 출력 |
| `__eq__` | `equals()` | `==` 비교 |
| `__hash__` | `hashCode()` | Set/Dict 키로 사용 |
| `__len__` | `.size()` | `len()` 호출 시 |
| `__repr__` | `toString()` (디버그용) | 디버깅 출력 |

> **요약: 던더는 직접 "발명"하지 말고, Python이 정해둔 것만 오버라이드해서 쓴다.**

### 실무에서 자주 오버라이드하는 던더

**자주 (TOP 5):**
- `__init__` — 생성자 (거의 항상)
- `__str__` — `print()` 할 때 보기 좋게 출력
- `__repr__` — 디버깅용 출력
- `__eq__` + `__hash__` — 객체 비교, Set/Dict 키로 쓸 때

**가끔:**
- `__len__` — `len(obj)` 지원
- `__getitem__` — `obj[0]` 같은 인덱스 접근
- `__enter__` / `__exit__` — `with` 문 (Java의 try-with-resources)

> 전체 목록은 외울 필요 없다. **BaseModel을 쓰면 `__init__`, `__str__`, `__eq__`, `__repr__`을 이미 다 만들어주기 때문에** 직접 오버라이드할 일이 거의 없다.

---

## frozen의 원리 — 어떻게 불변이 되는가?

`model_config = {"frozen": True}`를 설정하면, Pydantic이 내부적으로 `__setattr__`을 오버라이드해서 값 대입을 막는다.

```python
# Pydantic이 내부적으로 하는 일 (간략화)
class ImmutableMovie(BaseModel):
    def __setattr__(self, name, value):
        raise ValidationError("Instance is frozen")  # 대입 시도하면 에러
```

Python에서 `obj.title = "값"`을 실행하면 내부적으로 `obj.__setattr__("title", "값")`이 호출된다.
frozen=True는 이 `__setattr__`에서 **무조건 에러를 던지도록** 재정의하는 것이다.

```python
# 흐름 정리
movie.title = "변경"
# → Python이 movie.__setattr__("title", "변경") 호출
# → frozen이면: ValidationError! (차단)
# → frozen 아니면: 정상 대입
```

| | 기본 BaseModel | frozen=True |
|---|---|---|
| `__setattr__` 동작 | 값 대입 허용 | 에러 발생 (차단) |
| Java 비유 | `@Data` (setter 있음) | `record` / `@Value` (final 필드) |
| 값 변경 | 가능 | 불가능 |

> **결국 던더 오버라이드의 실전 활용 사례다.** Pydantic이 `__setattr__`이라는 던더를 재정의해서 setter를 차단하는 원리.

---

## model_config 주요 옵션

frozen 외에도 설정할 수 있는 옵션이 많다.

| 옵션 | 기본값 | 효과 | Java 비유 |
|------|--------|------|----------|
| `frozen=True` | False | setter 차단 (불변) | `record` / `@Value` |
| `strict=True` | False | 타입 자동변환 차단 (`"123"` → `int` 안 됨) | 엄격한 타입 검사 |
| `extra="forbid"` | `"ignore"` | 정의 안 한 필드 넣으면 에러 | 클래스에 없는 필드 거부 |
| `str_strip_whitespace=True` | False | 문자열 앞뒤 공백 자동 제거 | `.trim()` 자동 적용 |

### extra="forbid" — Java 개발자가 반드시 알아야 할 차이점

Java에서는 클래스에 없는 필드를 넣으면 **컴파일 에러**라 애초에 불가능하다.
하지만 Python은 동적 언어라서 **기본적으로 허용(무시)**해버린다.

```python
class Movie(BaseModel):
    title: str

# 기본값("ignore") → 에러 없이 foo, bar를 무시하고 생성됨!
movie = Movie(title="인셉션", foo="??", bar=123)  # 정상 동작 (Java에서는 말이 안 되는 상황)

# extra="forbid" → Java처럼 없는 필드 넣으면 에러
class StrictMovie(BaseModel):
    model_config = {"extra": "forbid"}
    title: str

movie = StrictMovie(title="인셉션", foo="??")  # ValidationError!
```

### 실무 권장 조합

```python
class AgentResponse(BaseModel):
    model_config = {
        "frozen": True,          # setter 차단 (불변)
        "extra": "forbid",       # 정의 안 한 필드 거부 (Java처럼)
    }
```

> **Java 개발자라면 `extra="forbid"`는 거의 필수.** 안 붙이면 오타나 잘못된 필드가 조용히 무시되어 버그 찾기가 어려워진다.

---

## 핵심 정리

1. **구조화된 출력** = 모델 응답을 미리 정의한 스키마대로 받아내는 것
2. **`with_structured_output(스키마)`** 메서드로 구조화 전용 래퍼 모델 생성
3. **Pydantic**: Python 기본 추천. 타입 안전, IDE 지원, 객체 접근
4. **JSON Schema**: 언어 중립, 동적 스키마, 외부 시스템 연동
5. **Field(description=...)은 LLM이 읽는 프롬프트** — 구체적으로 쓸수록 정확도 상승
6. **던더(`__xxx__`)는 Python 예약 규칙** — 직접 만들지 말고 오버라이드만
