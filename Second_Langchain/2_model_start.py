from dotenv import load_dotenv
import os

if not load_dotenv():
    print(".env 파일을 찾을 수 없습니다!")

from langchain_openai import ChatOpenAI

OPEN_API_KEY = os.environ["OPEN_API_KEY"]

# 공통 모델 (옵션 종합)
model = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=OPEN_API_KEY,
    temperature=0.1,
    max_tokens=500,
    timeout=30,
)

question = "사과의 매력을 한 문장으로 표현해줘."

# ===== 1. Temperature 비교 =====
print("=" * 50)
print("[1] Temperature 비교")
print("=" * 50)

model_temp_0 = ChatOpenAI(model="gpt-4o-mini", api_key=OPEN_API_KEY, temperature=0.0)
model_temp_1 = ChatOpenAI(model="gpt-4o-mini", api_key=OPEN_API_KEY, temperature=1.0)

print(f"\n[Temperature 0.0] {model_temp_0.invoke(question).content}")
print(f"[Temperature 1.0] {model_temp_1.invoke(question).content}")

# ===== 2. invoke() - 기본 호출 =====
print("\n" + "=" * 50)
print("[2] invoke() - 기본 호출")
print("=" * 50)

response = model.invoke(question)
print(f"\n응답: {response.content}")
print(f"토큰: {response.usage_metadata}")

# ===== 3. stream() - 스트리밍 출력 =====
print("\n" + "=" * 50)
print("[3] stream() - 실시간 스트리밍")
print("=" * 50)
print()

for token in model.stream("앵무새가 말을 따라하는 이유를 간단히 설명해줘."):
    print(token.content, end="", flush=True)
print()

# ===== 4. batch() - 일괄 처리 =====
print("\n" + "=" * 50)
print("[4] batch() - 여러 질문 병렬 처리")
print("=" * 50)

questions = [
    "사과를 한 단어로 표현하면?",
    "바나나를 한 단어로 표현하면?",
    "포도를 한 단어로 표현하면?",
]

responses = model.batch(questions, config={"max_concurrency": 3})
for q, r in zip(questions, responses):
    print(f"\n질문: {q}")
    print(f"답변: {r.content}")
