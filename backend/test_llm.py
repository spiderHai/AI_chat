from langchain_community.chat_models.tongyi import ChatTongyi
from dotenv import load_dotenv
import os

load_dotenv()

# 初始化模型
llm = ChatTongyi(
    dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
    model_name="qwen-turbo",
    temperature=0.1
)

# 调用模型
response = llm.invoke("你好，测试API是否可用")
print("模型回答：", response.content)
