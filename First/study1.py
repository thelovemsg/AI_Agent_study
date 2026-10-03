from dotenv import load_dotenv
import os

load_dotenv()  # 프로젝트 루트의 .env 파일에서 환경변수 로드

from openai import OpenAI

client = OpenAI(api_key=os.environ["OPEN_API_KEY"])

prompt = """
앵무새의 털 색상이 여러 개인 이유가 뭐야?
"""

response = client.responses.create(
    model="gpt-5-nano",
    reasoning={"effort" : "low"},
    input=[
        {
            "role" : "user",
            "content" : prompt
        }
    ],
)

print(response.output_text)
