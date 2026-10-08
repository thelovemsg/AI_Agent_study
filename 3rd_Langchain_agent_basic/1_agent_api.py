from typing import Any, Dict, List, Union
from langchain.tools import tool
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv 

import requests
import os

if not load_dotenv():
    print(".env 파일을 찾을 수 없습니다!")

OPEN_API_KEY = os.environ["OPEN_API_KEY"]

@tool
def fetch_aladin_bestseller_top10() -> Union[List[Dict[str, Any]], str]:
    """
    현재 시점의 알라딘 베스트셀러 Top 10 도서 목록을 조회하여 반환한다.
    반환값은 도서 정보가 담긴 딕셔너리의 리스트이거나, 호출 실패 시 에러 메시지(문자열)이다.
    """
    try:
        ttb_key = require_env("ALADIN_TTB_KEY")
        url = "http://www.aladin.co.kr/ttb/api/ItemList.aspx"
        params = {
            "ttbkey": ttb_key,
            "QueryType": "Bestseller",
            "MaxResults": 10,
            "start": 1,
            "SearchTarget": "Book",
            "output": "js",
            "Version": "20131101",
        }

        # API 호출 (타임아웃 10초 설정으로 무한 대기 방지)
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status() # HTTP 4xx, 5xx 에러 발생 시 예외 발생

        data = resp.json()

        # 모델이 핵심 정보에만 집중할 수 있도록, 전체 응답 중 도서 목록 10개만 슬라이싱하여 반환 (토큰 다이어트)
        return data.get("item", [])[:10]

    except Exception as e:
        # 에러가 발생해도 프로그램이 종료되지 않고, 모델에게 실패 원인을 텍스트로 알려줌 (우아한 실패)
        return f"API 호출 중 오류가 발생하여 베스트셀러 정보를 가져오지 못했습니다. 원인: {str(e)}"

model = init_chat_model(
    "gpt-4o-mini",
    model_provider="openai",
    api_key=OPEN_API_KEY,
)


agent = create_agent(model, tools=[fetch_aladin_bestseller_top10])

response = agent.invoke(
    {"messages": [{"role": "user", "content": "지금 알라딘 베스트셀러 1위부터 3위까지 알려줘."}]}
)

print(response["messages"][-1].content)
