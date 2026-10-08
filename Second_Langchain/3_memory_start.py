# ============================================================
# 2_memory_start.py - LangChain Memory (대화 맥락 유지)
# 참고: https://wikidocs.net/331272 (2-4) Memory
#
# 핵심: LangChain의 '메모리'는 저장소가 아니다.
#       지금까지의 메시지를 리스트에 누적해서 매번 다시 보내는 것이 전부다.
# ============================================================

from dotenv import load_dotenv
import os

if not load_dotenv():
    print(".env 파일을 찾을 수 없습니다!")

from langchain_openai import ChatOpenAI

# 메시지 클래스 - 대화의 각 발화를 역할별로 담는 그릇
# 책에서는 `from langchain.messages import ...` 로 소개하지만 이 경로는 langchain 1.x 전용이다.
# langchain_core 경로는 0.3.x / 1.x 양쪽에서 모두 동작하므로 이쪽을 쓴다.
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# trim_messages: 토큰 예산에 맞춰 메시지를 잘라내는 유틸
# count_tokens_approximately: 실제 토크나이저를 돌리지 않고 토큰 수를 빠르게 어림잡는 함수
from langchain_core.messages.utils import trim_messages, count_tokens_approximately

OPEN_API_KEY = os.environ["OPEN_API_KEY"]

# 실습용 모델 - 기억 테스트는 정확성이 중요하므로 temperature를 낮게 잡는다
model = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=OPEN_API_KEY,
    temperature=0.1,
    max_tokens=300,  # 실습이므로 짧게 (비용 절약)
    timeout=30,
)


# ===== 1. 메모리가 없으면 어떻게 되나 =====
print("=" * 50)
print("[1] 메모리 없음 - 모델은 직전 대화를 모른다")
print("=" * 50)

# invoke() 호출은 매번 완전히 독립적이다. API 서버는 세션을 들고 있지 않다.
model.invoke("저는 Jay라고 합니다.")  # 이름을 알려줘도
answer = model.invoke("제 이름이 뭐라고 했죠?")  # 다음 호출은 그 사실을 모른다

print("\n사용자: 제 이름이 뭐라고 했죠?")
print(f"모델  : {answer.content}")


# ===== 2. 방법 1) 메시지 객체로 맥락 전달 =====
print("\n" + "=" * 50)
print("[2] 방법 1) 메시지 객체 (SystemMessage / HumanMessage / AIMessage)")
print("=" * 50)

# SystemMessage = 개발자가 부여하는 역할·규칙 프롬프트 (사용자에게는 보이지 않음)
# HumanMessage  = 사용자 입력
# AIMessage     = 모델이 생성한 과거 답변 (이걸 다시 넣어줘야 '기억'이 된다)
messages = [
    SystemMessage("당신은 친절한 조교입니다. 답변은 2문장 이내로 해주세요."),
    HumanMessage("안녕하세요. 저는 Jay라고 합니다."),
    AIMessage("안녕하세요 Jay님, 반갑습니다. 무엇을 도와드릴까요?"),
    HumanMessage("제가 방금 제 이름을 뭐라고 했죠?"),
]

# 리스트를 그대로 invoke()에 전달한다. 모델은 이 전체를 읽고 다음 답변을 만든다.
answer = model.invoke(messages)

print("\n사용자: 제가 방금 제 이름을 뭐라고 했죠?")
print(f"조교  : {answer.content}")  # AIMessage가 입력에 있으니 이름을 안다


# ===== 3. 방법 2) 딕셔너리로 맥락 전달 =====
print("\n" + "=" * 50)
print("[3] 방법 2) 딕셔너리 (role / content)")
print("=" * 50)

# 클래스를 쓰지 않고 role/content 딕셔너리로 넘겨도 내부에서 알아서 변환된다.
# 장점: JSON 직렬화가 쉬워서 DB에 대화 기록을 저장/조회하기 유리하다.
messages = [
    {"role": "system", "content": "당신은 유능한 로켓 전문가입니다."},
    {"role": "human", "content": "안녕하세요. 궁금한 게 있어요!"},
    {"role": "ai", "content": "로켓 관련 무엇이든 물어보세요."},
    {"role": "human", "content": "고체 연료와 액체 연료의 차이를 한 문장으로 설명해주세요."},
]

answer = model.invoke(messages)
print(f"\n전문가: {answer.content}")


# ===== 4. 멀티턴 대화 누적 - 메모리의 실체 =====
print("\n" + "=" * 50)
print("[4] 멀티턴 누적 - 입력 토큰이 턴마다 늘어나는 것을 확인")
print("=" * 50)

# history 리스트 하나가 곧 '메모리'다. 별도의 Memory 객체가 필요 없다.
history = [SystemMessage("당신은 친절한 조교입니다. 답변은 1~2문장으로 짧게 해주세요.")]

user_turns = [
    "안녕하세요, 저는 Jay이고 로켓 엔진을 공부하고 있어요.",
    "제가 뭘 공부한다고 했죠?",
    "그 분야를 처음 배울 때 뭐부터 보면 좋을까요?",
    "제 이름도 기억하세요?",
]

for turn in user_turns:
    history.append(HumanMessage(turn))  # (1) 사용자 발화를 누적
    answer = model.invoke(history)      # (2) 리스트 '전체'를 전달
    history.append(answer)              # (3) 모델 답변도 누적 <- 이 줄이 핵심

    print(f"\n사용자: {turn}")
    print(f"조교  : {answer.content}")
    # 턴이 쌓일수록 input_tokens가 계속 증가한다 = 비용이 누적된다
    print(f"        (메시지 {len(history)}개 / 입력 토큰 {answer.usage_metadata['input_tokens']})")


# ===== 5. 전략 1) 슬라이딩 윈도우 - 최근 N개만 유지 =====
print("\n" + "=" * 50)
print("[5] 전략 1) 슬라이딩 윈도우 - 최근 N개만 유지")
print("=" * 50)


def sliding_window(messages, n=4):
    """시스템 메시지는 고정하고, 나머지는 최근 n개만 남긴다."""
    system = [m for m in messages if isinstance(m, SystemMessage)]
    rest = [m for m in messages if not isinstance(m, SystemMessage)]
    return system + rest[-n:]  # 음수 인덱스 슬라이싱 = 뒤에서 n개


windowed = sliding_window(history, n=4)

print(f"\n전체 {len(history)}개 -> 윈도우 적용 후 {len(windowed)}개")
print(f"토큰: {count_tokens_approximately(history)} -> {count_tokens_approximately(windowed)}")

# 단점 확인: 대화 초반에 말한 이름은 윈도우 밖으로 밀려나 사라졌다
windowed.append(HumanMessage("제 이름이 뭐였죠?"))
answer = model.invoke(windowed)
print("\n사용자: 제 이름이 뭐였죠?")
print(f"조교  : {answer.content}")  # <- 초반 정보가 잘려서 모를 가능성이 높다


# ===== 6. 전략 2) 토큰 예산 기반 트리밍 (권장 기본값) =====
print("\n" + "=" * 50)
print("[6] 전략 2) trim_messages - 토큰 예산 기반 트리밍")
print("=" * 50)

# 턴 수가 아니라 '토큰 수'를 기준으로 자른다. 비용 상한을 직접 통제할 수 있다.
trimmed = trim_messages(
    history,
    strategy="last",                        # 오래된 것을 버리고 최근을 유지
    token_counter=count_tokens_approximately,  # 토큰 계산 함수
    max_tokens=200,                         # 입력 토큰 상한 (실습용으로 일부러 작게)
    include_system=True,                    # 시스템 메시지는 잘리지 않게 고정(핀)
    start_on="human",                       # 잘린 결과가 반드시 사람 질문으로 시작하도록 보장
    end_on=("human", "tool"),               # 마지막이 사람 질문으로 끝나도록 보장
)

print(f"\n전체 {len(history)}개 -> 트리밍 후 {len(trimmed)}개")
print(f"토큰: {count_tokens_approximately(history)} -> {count_tokens_approximately(trimmed)} (상한 200)")
print("\n남은 메시지 구성:")
for m in trimmed:
    # m.type은 'system' / 'human' / 'ai' 를 반환한다
    print(f"  [{m.type}] {m.content[:40]}...")

answer = model.invoke(trimmed)
print(f"\n조교  : {answer.content}")


# ===== 7. 전략 3) 요약 + 최근 대화 유지 (하이브리드) =====
print("\n" + "=" * 50)
print("[7] 전략 3) 요약 + 최근 대화 유지 (하이브리드)")
print("=" * 50)


def summarize(messages):
    """과거 대화를 모델에게 요약시켜 한 덩어리로 압축한다."""
    # 대화 원문을 "역할: 내용" 한 줄씩으로 펼쳐서 요약 요청에 넣는다
    transcript = "\n".join(f"{m.type}: {m.content}" for m in messages)
    prompt = [
        SystemMessage(
            "아래 대화를 3줄 이내로 요약해라. "
            "사용자의 이름, 목표, 제약조건은 반드시 포함해라."
        ),
        HumanMessage(transcript),
    ]
    return model.invoke(prompt).content


# 오래된 대화(앞부분)는 요약하고, 최근 2개는 원문 그대로 둔다
old_part, recent_part = history[1:-2], history[-2:]
summary = summarize(old_part)

print(f"\n[요약본]\n{summary}")

# 요약본을 시스템 메시지에 고정해 둔다 -> 잘려나가지 않는다
hybrid = [
    SystemMessage(
        "당신은 친절한 조교입니다. 답변은 1~2문장으로 짧게 해주세요.\n\n"
        f"[이전 대화 요약]\n{summary}"
    ),
    *recent_part,
    HumanMessage("제 이름이 뭐였죠?"),
]

print(f"\n메시지 {len(hybrid)}개 / 토큰 {count_tokens_approximately(hybrid)}")

answer = model.invoke(hybrid)
print("\n사용자: 제 이름이 뭐였죠?")
print(f"조교  : {answer.content}")  # <- 요약본에 이름이 남아 있으므로 기억한다
