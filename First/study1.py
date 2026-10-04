from dotenv import load_dotenv
import os

if not load_dotenv():
    print(".env 파일을 찾을 수 없습니다!")

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
