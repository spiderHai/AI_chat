"""LLM 调用层 - 通义千问"""
import requests
from .config import DASHSCOPE_API_KEY, DASHSCOPE_API_URL


def call_qwen(prompt: str) -> str:
    """调用通义千问 qwen-turbo"""
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "qwen-turbo",
        "input": {
            "messages": [
                {"role": "user", "content": prompt}
            ]
        },
        "parameters": {}
    }
    resp = requests.post(DASHSCOPE_API_URL, json=payload, headers=headers, timeout=30)
    if resp.status_code != 200:
        return f"API调用失败: {resp.status_code} {resp.text}"
    result = resp.json()
    if "output" in result and "text" in result["output"]:
        return result["output"]["text"]
    return "无法获取AI回复"
