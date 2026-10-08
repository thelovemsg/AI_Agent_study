from langchain.tools import tool

from dotenv import load_dotenv
import os

if not load_dotenv():
    print(".env 파일을 찾을 수 없습니다!")

@tool
def get_weather(location: str) -> str:
    """특정 지역의 날씨 정보를 제공합니다."""
    return f"{location}의 날씨는 맑고, 영하 2도입니다"

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

OPEN_API_KEY = os.environ["OPEN_API_KEY"]

model = init_chat_model(
    "gpt-4o-mini",
    model_provider="openai",
    api_key=OPEN_API_KEY,
)
agent = create_agent(model, tools=[get_weather])

result = agent.invoke({
    "messages": [
        {"role": "user", "content": "서울 날씨 어때요?"}
    ]
})

print(result["messages"][-1].content)

print("="*50);
print("tool_calls와 ToolMessage");
print("="*50);
print("""
1. 계획 수립 : 모델이 질문을 분석한 뒤 도구가 필요하다고 판단하면, 직접 텍스트 답변을 적는 대신 AIMessage 안에 "이 도구를 이렇게 실행해 줘"라는 구체적인 계획(tool_calls)을 남깁니다. (이때 모델의 자연어 텍스트 답변은 비어있습니다.)
2. 실제 실행 : 런타임 환경은 모델의 계획을 확인하고 실제 파이썬 함수(get_weather)를 실행합니다. 그리고 그 반환값을 ToolMessage라는 특별한 상자에 담아 다시 대화 기록에 추가하죠.
3. 최종 답변 생성 : 모델은 방금 추가된 ToolMessage(예: "서울의 날씨는 맑고, 영하 2도입니다")를 읽고, 비로소 사용자에게 전달할 최종 자연어 답변을 완성합니다.
""")