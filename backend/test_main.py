"""
后端测试文件
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    """测试健康检查端点"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


def test_chat_empty_question():
    """测试空问题处理"""
    response = client.post("/api/chat", json={"question": ""})
    assert response.status_code == 400


def test_chat_valid_question():
    """测试有效问题"""
    response = client.post("/api/chat", json={"question": "你好"})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "timestamp" in data
    assert isinstance(data["answer"], str)
