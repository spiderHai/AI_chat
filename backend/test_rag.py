"""
RAG 系统测试脚本
"""
import requests
import json

BASE_URL = "http://localhost:8001"

def test_add_documents():
    """测试添加文档"""
    print("=== 测试添加文档 ===")

    docs = [
        {
            "text": "我们公司提供 AI 聊天机器人服务，支持智能客服、知识库管理等功能。",
            "title": "产品介绍"
        },
        {
            "text": "基础版价格 ¥99/月，专业版 ¥299/月，企业版定制价格。",
            "title": "价格方案"
        },
        {
            "text": "支持云端部署、私有化部署和混合部署三种方式。",
            "title": "部署方式"
        }
    ]

    for doc in docs:
        resp = requests.post(f"{BASE_URL}/add", json=doc)
        print(f"✓ {doc['title']}: {resp.json()}")

def test_query():
    """测试查询"""
    print("\n=== 测试 RAG 查询 ===")

    questions = [
        "你们提供什么服务？",
        "价格是多少？",
        "支持哪些部署方式？"
    ]

    for q in questions:
        print(f"\n问题: {q}")
        resp = requests.post(f"{BASE_URL}/query", json={"question": q, "top_k": 2})
        result = resp.json()
        print(f"答案: {result['answer']}")
        print(f"来源: {result['sources']}")

def test_stats():
    """测试统计"""
    print("\n=== 统计信息 ===")
    resp = requests.get(f"{BASE_URL}/stats")
    print(resp.json())

if __name__ == "__main__":
    test_add_documents()
    test_query()
    test_stats()
