from langchain.tools import tool
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from dotenv import load_dotenv 
import os

if not load_dotenv():
    print(".env 파일을 찾을 수 없습니다!")

OPEN_API_KEY = os.environ["OPEN_API_KEY"]

@tool
def add(a: int, b: int) -> int:
        """`a`와 `b` 덧셈.

        Args:
            a: First int
            b: Second int
        """
        return a+b;

@tool
def multiply(a: int, b: int) -> int:
    """`a`와 `b` 곱셈.

    Args:
        a: First int
        b: Second int
    """
    return a*b

@tool
def divide(a: int, b: int) -> float:
        """`a`와 `b` 나눗셈.

        Args:
            a: First int
            b: Second int
        """
        return a/batch

model = init_chat_model(
    "gpt-4o-mini",
    model_provider="openai",
    api_key=OPEN_API_KEY,
)

tools = [add, multiply, divide]

# 1. InMemorySaver 객체를 생성하여 checkpointer 인자로 주입합니다.
agent = create_agent(
    model, 
    tools,
    checkpointer=InMemorySaver(),
)

# 2. config 딕셔너리에 thread_id를 "1"로 고정합니다. 이 값이 기억을 불러오는 열쇠가 됩니다.
cfg = {"configurable": {"thread_id": "1"}}

# 첫 번째 턴: 사용자 정보(이름) 전달
response = agent.invoke(
    {"messages": [{"role": "user", "content": "안녕하세요! 저는 Bloom AI의 Jay 입니다."}]},
    cfg,
)

print("[에이전트의 답변]:", response["messages"][-1].content)

# 두 번째 턴: 이전 맥락을 바탕으로 질문하기 (동일한 thread_id 사용)
response = agent.invoke(
    {"messages": [{"role": "user", "content": "방금 제가 제 이름을 뭐라고 했죠?"}]},
    cfg,
)
print("[에이전트의 답변]:", response["messages"][-1].content)

# 세 번째 턴: thread_id를 "2"로 변경하여 완전히 새로운 채팅방(세션)을 엽니다.
response = agent.invoke(
    {"messages": [{"role": "user", "content": "지금까지 우리가 무슨 얘기를 나눴죠?"}]},
    {"configurable": {"thread_id": "2"}},  # 열쇠 변경!
)
print("[에이전트의 답변]:", response["messages"][-1].content)

# 1번 방의 대화 내역을 다시 불러옵니다.
response = agent.invoke(
    {"messages": [{"role": "user", "content": "지금까지 무슨 얘기 나눴죠?"}]},
    {"configurable": {"thread_id": "1"}},
)

# 세션에 누적된 전체 메시지 히스토리를 하나씩 뜯어봅니다.
for i, msg in enumerate(response["messages"], start=1):
    print(f"--- Message {i} ({msg.type}) ---")
    print(msg.content)
    print()
