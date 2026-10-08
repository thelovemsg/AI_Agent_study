# ============================================================
# 4_langsmith_start.py - LangSmith (추적 / 평가 / 모니터링)
# 참고: 2-5) 랭스미스
#
# 핵심: 코드를 고치지 않는다. 환경변수만 켜면 모든 LLM 호출이 자동으로 기록된다.
# ============================================================

# ===== 0. 설정 순서가 중요하다 =====
# LangSmith 설정은 langchain 모델을 임포트/초기화하기 '전'에 잡혀 있어야 한다.
# 그래서 이 파일은 import 문이 위아래로 나뉘어 있다.

from dotenv import load_dotenv
import os

if not load_dotenv():
    print(".env 파일을 찾을 수 없습니다!")

# 추적 기능 ON
# 책은 LANGCHAIN_TRACING_V2 를 쓰지만, 현재 권장 이름은 LANGSMITH_TRACING 이다. (둘 다 동작)
os.environ["LANGSMITH_TRACING"] = "true"

# 실행 로그를 묶는 단위. 대시보드에서 이 이름의 프로젝트로 모인다.
os.environ["LANGSMITH_PROJECT"] = "AI_Agent_study"

# LANGSMITH_API_KEY는 .env에서 읽어온다.
# 책처럼 코드에 키를 직접 적으면 git에 올라갈 위험이 있으므로 절대 하지 않는다.
if not os.environ.get("LANGSMITH_API_KEY"):
    print("[경고] LANGSMITH_API_KEY가 없습니다. .env에 추가하세요.")
    print("       추적 없이 실행은 되므로, 일단 끄고 진행합니다.\n")
    os.environ["LANGSMITH_TRACING"] = "false"

# ===== 설정이 끝난 뒤에 모델을 임포트한다 =====
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage
from langsmith import traceable

OPEN_API_KEY = os.environ["OPEN_API_KEY"]


# ===== 1. init_chat_model - 모델을 문자열 하나로 만들기 =====
print("=" * 50)
print("[1] init_chat_model 으로 모델 생성")
print("=" * 50)

# 지금까지는 ChatOpenAI를 직접 썼지만, init_chat_model은 provider를 가려준다.
# 모델 문자열만 바꾸면 Anthropic/Google로 교체할 수 있다.
#
# 주의: init_chat_model은 기본적으로 OPENAI_API_KEY 환경변수를 찾는다.
#      우리 .env의 이름은 OPEN_API_KEY이므로 api_key를 명시해서 넘긴다.
model = init_chat_model(
    "gpt-4o-mini",            # 책은 "gpt-5-nano". 모델명만 바꾸면 된다
    model_provider="openai",  # 생략 가능하지만 명시하는 쪽이 안전하다
    api_key=OPEN_API_KEY,
    temperature=0.1,
    max_tokens=300,
)

response = model.invoke("랭스미스가 무엇인지 한 문장으로 설명해줘.")
print(f"\n답변: {response.content}")
print(f"토큰: {response.usage_metadata}")


# ===== 2. run_name / tags / metadata 붙이기 =====
print("\n" + "=" * 50)
print("[2] 추적에 이름과 태그 붙이기")
print("=" * 50)

# 호출이 쌓이면 대시보드에서 어느 게 무엇인지 구분이 안 된다.
# config로 이름·태그·메타데이터를 달아두면 검색과 필터링이 가능해진다.
response = model.invoke(
    "LangSmith로 추적하면 좋은 점 두 가지만 짧게 알려줘.",
    config={
        "run_name": "langsmith-intro",          # 대시보드에 표시될 실행 이름
        "tags": ["lesson4", "smoke-test"],      # 필터용 태그
        "metadata": {"lesson": "2-5", "env": "local"},  # 임의의 부가 정보
    },
)
print(f"\n답변: {response.content}")


# ===== 3. 멀티턴 호출은 메시지 전체가 기록된다 =====
print("\n" + "=" * 50)
print("[3] 멀티턴 - 대시보드에서 입력 메시지 전체를 볼 수 있다")
print("=" * 50)

# 3차 학습(Memory)에서 만든 누적 패턴. LangSmith를 켜두면
# '어떤 메시지들이 실제로 모델에 들어갔는지'를 눈으로 확인할 수 있다.
# 트리밍이 의도대로 동작하는지 검증할 때 이게 가장 확실한 방법이다.
history = [SystemMessage("당신은 친절한 조교입니다. 1~2문장으로 짧게 답하세요.")]

for turn in ["저는 Jay이고 로켓 엔진을 공부해요.", "제가 뭘 공부한다고 했죠?"]:
    history.append(HumanMessage(turn))
    answer = model.invoke(history, config={"run_name": f"multiturn-{len(history)//2}"})
    history.append(answer)

    print(f"\n사용자: {turn}")
    print(f"조교  : {answer.content}")
    print(f"        (입력 토큰 {answer.usage_metadata['input_tokens']})")


# ===== 4. @traceable - 내가 만든 함수도 추적하기 =====
print("\n" + "=" * 50)
print("[4] @traceable - LLM 호출이 아닌 내 함수도 추적")
print("=" * 50)


# LLM 호출만 기록하면 '전처리에서 뭘 잘못 넣었는지'는 안 보인다.
# @traceable을 붙이면 일반 함수도 실행 경로에 함께 기록된다.
@traceable(name="build_review_prompt")
def build_review_prompt(items: list[str]) -> list:
    """이력서 항목 리스트를 리뷰 프롬프트로 조립한다."""
    bullets = "\n".join(f"- {it}" for it in items)
    return [
        SystemMessage("당신은 이력서 첨삭 전문가입니다. 각 항목을 한 줄로 평가하세요."),
        HumanMessage(f"다음 경력 항목을 검토해주세요:\n{bullets}"),
    ]


@traceable(name="review_resume")
def review_resume(items: list[str]) -> str:
    """프롬프트 조립 + LLM 호출을 하나의 추적 단위로 묶는다."""
    prompt = build_review_prompt(items)  # 중첩 호출은 트리 구조로 기록된다
    return model.invoke(prompt).content


result = review_resume([
    "결제 API 개발",
    "결제 API 응답 420ms -> 110ms 개선",
])
print(f"\n{result}")

print("\n" + "=" * 50)
print("대시보드에서 확인:  https://smith.langchain.com")
print(f"프로젝트: {os.environ['LANGSMITH_PROJECT']}")
print("=" * 50)
