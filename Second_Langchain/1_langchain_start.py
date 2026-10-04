from dotenv import load_dotenv
import os

if not load_dotenv():
    print(".env 파일을 찾을 수 없습니다!")

from langchain_openai import ChatOpenAI

model = ChatOpenAI(model="gpt-4o-mini", api_key=os.environ["OPEN_API_KEY"])

response = model.invoke("앵무새의 털 색상이 여러 개인 이유가 뭐야?")

print(response)
print(response.content)
