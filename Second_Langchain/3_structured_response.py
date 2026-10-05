from dotenv import load_dotenv
import os
import json

if not load_dotenv():
    print(".env 파일을 찾을 수 없습니다!")

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field  # BaseModel=Java record, Field=@Schema/@NotNull 같은 필드 어노테이션
from typing import Optional, Literal   # Optional=@Nullable, Literal=enum

OPEN_API_KEY = os.environ["OPEN_API_KEY"]

model = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=OPEN_API_KEY,
    temperature=0.1,
    max_tokens=500,
    timeout=30,
)


# ===== 1. Pydantic 방식 - 구조화된 출력 =====
print("=" * 50)
print("[1] Pydantic 방식 - 구조화된 출력")
print("=" * 50)


class Movie(BaseModel):  # BaseModel 상속 = Java의 extends. 생성자/getter/타입검증/dict변환 자동 제공
    """상세한 영화 정보."""
    title: str = Field(description="영화의 제목 (예: 인셉션)")                          # str = Java String
    year: Optional[int] = Field(default=None, description="개봉 연도. 모르면 None.")     # Optional = null 허용
    genre: Literal["액션", "로맨스", "SF", "코미디", "기타"] = Field(description="영화의 장르")  # Literal = enum처럼 값 제한
    director: str = Field(description="영화 감독 이름")
    rating: float = Field(description="영화 평점 (10점 만점 기준)")                      # float = Java double
    # Field의 description은 단순 주석이 아니라 LLM이 읽는 프롬프트. 구체적으로 쓸수록 정확도 상승.


model_with_pydantic = model.with_structured_output(Movie)  # 이 스키마 규격대로 파싱하는 래퍼 모델 생성
response = model_with_pydantic.invoke("영화 인셉션에 대해 설명해 주세요")

print(f"\n전체 응답: {response}")
print(f"\n제목: {response.title} (타입: {type(response.title).__name__})")
print(f"연도: {response.year} (타입: {type(response.year).__name__})")
print(f"장르: {response.genre} (타입: {type(response.genre).__name__})")
print(f"감독: {response.director} (타입: {type(response.director).__name__})")
print(f"평점: {response.rating} (타입: {type(response.rating).__name__})")
print(f"\ndict 변환: {response.model_dump()}")        # Java의 ObjectMapper 역할
print(f"JSON 변환: {response.model_dump_json()}")      # JSON 문자열 직렬화


# ===== 2. frozen - setter 차단 (불변 객체) =====
print("\n" + "=" * 50)
print("[2] frozen=True (setter 차단, Java의 record/@Value)")
print("=" * 50)


class ImmutableMovie(BaseModel):
    model_config = {"frozen": True}  # 이 한 줄로 setter 차단. Java의 record/Lombok @Value와 동일
    title: str = Field(description="영화의 제목")
    director: str = Field(description="영화 감독 이름")


immutable = ImmutableMovie(title="인셉션", director="크리스토퍼 놀란")
print(f"\n제목: {immutable.title}")

try:
    immutable.title = "다른 영화"  # frozen이라 에러 발생
except Exception as e:
    print(f"[setter 차단됨] {type(e).__name__}: {e}")

# 비교: 기본 BaseModel은 setter 가능
mutable = Movie(title="인셉션", year=2010, genre="SF", director="크리스토퍼 놀란", rating=8.8)
mutable.title = "변경된 제목"
print(f"\n기본 BaseModel은 setter 가능: {mutable.title}")


# ===== 3. JSON Schema 방식 =====
print("\n" + "=" * 50)
print("[3] JSON Schema 방식 - 구조화된 출력")
print("=" * 50)

json_schema = {
    "title": "Movie",
    "description": "A movie with details",
    "type": "object",
    "properties": {
        "title":    {"type": "string",  "description": "The title of the movie"},
        "year":     {"type": "integer", "description": "The year the movie was released"},
        "director": {"type": "string",  "description": "The director of the movie"},
        "rating":   {"type": "number",  "description": "The movie's rating out of 10"},
    },
    "required": ["title", "director", "rating"],  # year 빠짐 = Optional과 같은 효과
}

model_with_json = model.with_structured_output(json_schema)
response_json = model_with_json.invoke("영화 인터스텔라에 대해서 소개해 주세요")

print(f"\n전체 응답: {response_json}")
print(f"\n제목: {response_json['title']}")   # dict라서 ['key']로 접근
print(f"감독: {response_json['director']}")
print(f"평점: {response_json['rating']}")


# ===== 4. 두 방식 비교 =====
print("\n" + "=" * 50)
print("[4] 반환 타입 비교")
print("=" * 50)

print(f"\nPydantic    → {type(response).__name__} 객체 → response.title     = '{response.title}'")
print(f"JSON Schema → {type(response_json).__name__} 딕셔너리 → response['title']  = '{response_json['title']}'")
