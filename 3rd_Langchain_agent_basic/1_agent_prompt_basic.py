from langchain.tools import tool
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
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
agent = create_agent(
    model, 
    tools,
    system_prompt="당신은 유능한 수학 선생님입니다. 추측하지 말고, 계산 시 모든 단계에서 tool들을 이용하시오."
)

result = agent.invoke(
    {"messages" : [
        {"role" : "user", "content" : "42 + 3 * 23은 뭔가요?"}    
    ]
})

print(result)