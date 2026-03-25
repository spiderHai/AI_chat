"""
大模型 API 调用封装 (LLM Client)

核心知识点：
1. Messages 格式 — 大模型 API 的标准输入格式
2. 模型参数 — temperature, top_p, max_tokens 等控制生成行为
3. 错误处理与重试 — 网络不稳定时的容错机制
4. 流式输出 (Streaming) — 逐字返回，提升用户体验
5. Token 计费意识 — 理解 token 和成本的关系
6. 多模型切换 — 不同场景用不同模型
"""

import time
import json
import requests
from typing import List, Optional, Generator
from enum import Enum
from .config import DASHSCOPE_API_KEY, DASHSCOPE_API_URL
from .logger import get_logger, Timer

logger = get_logger("llm")


# ============================================================
# 知识点1: 模型选择
# ============================================================
# 不同模型有不同的能力和价格：
# - qwen-turbo: 速度快、便宜，适合简单任务（分类、提取）
# - qwen-plus: 能力更强，适合复杂推理
# - qwen-max: 最强，适合需要高质量输出的场景
#
# 实际项目中，不是所有请求都用最贵的模型。
# 比如"分析问题意图"用 turbo 就够了，"生成最终回答"才用 plus。

class ModelType(Enum):
    TURBO = "qwen-turbo"       # 快速、便宜
    PLUS = "qwen-plus"         # 均衡
    MAX = "qwen-max"           # 最强


# ============================================================
# 知识点2: 模型参数 (Parameters)
# ============================================================
# temperature (0~2):
#   控制输出的"随机性"。
#   0 = 每次输出几乎一样（适合事实性问答）
#   1 = 正常随机性
#   >1 = 更有创意但可能胡说（适合写故事）
#
# top_p (0~1):
#   另一种控制随机性的方式，和 temperature 二选一调就行。
#   0.1 = 只从概率最高的10%词汇中选
#   1.0 = 从所有词汇中选
#
# max_tokens:
#   限制输出的最大长度。1个中文字 ≈ 1-2个token。
#   设太小会导致回答被截断，设太大会浪费钱。

DEFAULT_PARAMS = {
    "temperature": 0.7,   # RAG 场景建议 0.3~0.7，别太高
    "top_p": 0.8,
    "max_tokens": 1500,
}


# ============================================================
# 知识点3: LLM 客户端封装
# ============================================================
# 为什么要封装？直接 requests.post 不行吗？
#
# 当然可以，但实际项目中你会遇到：
# - API 偶尔超时或返回500，需要自动重试
# - 不同场景要用不同模型和参数
# - 需要统计 token 用量和成本
# - 需要支持流式输出
# - 需要统一的错误处理
#
# 封装成类，这些逻辑写一次，到处复用。

class LLMClient:
    """大模型 API 客户端

    使用方式：
        client = LLMClient()

        # 简单调用（兼容旧代码）
        result = client.chat("你好")

        # 带 messages 格式调用
        result = client.chat_with_messages([
            {"role": "system", "content": "你是助手"},
            {"role": "user", "content": "你好"}
        ])

        # 指定模型和参数
        result = client.chat("分析这个问题",
                             model=ModelType.PLUS,
                             temperature=0.3)
    """

    def __init__(self):
        self.api_key = DASHSCOPE_API_KEY
        self.api_url = DASHSCOPE_API_URL
        # 用量统计（生产环境可以接入监控系统）
        self.total_calls = 0
        self.total_errors = 0

    # --------------------------------------------------------
    # 知识点4: Messages 格式
    # --------------------------------------------------------
    # 几乎所有大模型 API（OpenAI、通义千问、Claude）都用这个格式：
    #
    # messages = [
    #     {"role": "system", "content": "你是..."},    ← 系统指令
    #     {"role": "user", "content": "用户说的话"},    ← 用户消息
    #     {"role": "assistant", "content": "AI的回复"}, ← AI历史回复
    #     {"role": "user", "content": "用户的新问题"},  ← 最新消息
    # ]
    #
    # 这个列表就是"对话历史"，大模型根据完整历史来生成回复。
    # 这也是为什么 AI 能"记住"之前说过什么——因为你每次都把历史传给它。

    def _build_payload(
        self,
        messages: List[dict],
        model: ModelType = ModelType.TURBO,
        **kwargs
    ) -> dict:
        """
        构建 API 请求体。

        DashScope 的格式和 OpenAI 略有不同：
        - DashScope: {"model": "...", "input": {"messages": [...]}, "parameters": {...}}
        - OpenAI:    {"model": "...", "messages": [...], "temperature": ...}

        但核心概念是一样的：模型名 + 消息列表 + 参数。
        """
        params = {**DEFAULT_PARAMS, **kwargs}
        return {
            "model": model.value,
            "input": {"messages": messages},
            "parameters": {
                "temperature": params.get("temperature", 0.7),
                "top_p": params.get("top_p", 0.8),
                "max_tokens": params.get("max_tokens", 1500),
                # result_format: "message" 让返回值也是 message 格式
                # 这样可以直接追加到对话历史中
                "result_format": "message",
            }
        }

    # --------------------------------------------------------
    # 知识点5: 错误处理与重试
    # --------------------------------------------------------
    # 大模型 API 是远程服务，可能出现：
    # - 网络超时 (Timeout)
    # - 服务过载 429 (Rate Limit) — 请求太频繁
    # - 服务器错误 500 (Internal Error)
    #
    # 重试策略：
    # - 指数退避 (Exponential Backoff): 第1次等1秒，第2次等2秒，第3次等4秒
    # - 只重试可恢复的错误（超时、429、500），不重试参数错误（400）
    # - 设置最大重试次数，避免无限循环

    def _call_api(
        self,
        messages: List[dict],
        model: ModelType = ModelType.TURBO,
        max_retries: int = 3,
        **kwargs
    ) -> dict:
        """带重试的 API 调用"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = self._build_payload(messages, model, **kwargs)
        timer = Timer()

        last_error = None
        for attempt in range(max_retries):
            try:
                self.total_calls += 1
                resp = requests.post(
                    self.api_url,
                    json=payload,
                    headers=headers,
                    timeout=30
                )

                # 成功
                if resp.status_code == 200:
                    result = resp.json()
                    self._log_usage(result, model, timer)
                    return result

                # 429 = 请求太频繁，等一会儿再试
                # 500/502/503 = 服务器临时故障，也可以重试
                if resp.status_code in (429, 500, 502, 503):
                    wait_time = (2 ** attempt)  # 指数退避: 1s, 2s, 4s
                    logger.warning(
                        "API 返回错误，准备重试",
                        model=model.value,
                        status_code=resp.status_code,
                        attempt=attempt + 1,
                        wait_seconds=wait_time,
                    )
                    time.sleep(wait_time)
                    last_error = f"HTTP {resp.status_code}: {resp.text}"
                    continue

                # 其他错误（400参数错误等）不重试，直接返回
                self.total_errors += 1
                logger.error(
                    "API 调用失败（不可重试）",
                    model=model.value,
                    status_code=resp.status_code,
                    duration_ms=timer.elapsed_ms(),
                )
                return {"error": f"API错误 {resp.status_code}: {resp.text}"}

            except requests.Timeout:
                wait_time = (2 ** attempt)
                logger.warning(
                    "API 请求超时，准备重试",
                    model=model.value,
                    attempt=attempt + 1,
                    wait_seconds=wait_time,
                )
                time.sleep(wait_time)
                last_error = "请求超时"

            except requests.ConnectionError as e:
                self.total_errors += 1
                logger.error("网络连接失败", model=model.value, error=str(e))
                return {"error": f"网络连接失败: {e}"}

        self.total_errors += 1
        logger.error(
            "API 重试耗尽",
            model=model.value,
            max_retries=max_retries,
            duration_ms=timer.elapsed_ms(),
        )
        return {"error": f"重试{max_retries}次后仍然失败: {last_error}"}

    # --------------------------------------------------------
    # 知识点6: 解析响应
    # --------------------------------------------------------
    # DashScope 返回格式（result_format="message" 时）：
    # {
    #   "output": {
    #     "choices": [{
    #       "message": {"role": "assistant", "content": "回复内容"},
    #       "finish_reason": "stop"
    #     }]
    #   },
    #   "usage": {
    #     "input_tokens": 100,    ← 输入消耗的 token
    #     "output_tokens": 50,    ← 输出消耗的 token
    #     "total_tokens": 150     ← 总计
    #   }
    # }
    #
    # 旧格式（不设 result_format 时）：
    # {"output": {"text": "回复内容"}}

    def _parse_response(self, result: dict) -> str:
        """从 API 响应中提取文本"""

        if "error" in result:
            return f"[错误] {result['error']}"

        output = result.get("output", {})

        # 新格式: output.choices[0].message.content
        choices = output.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "无法获取回复")

        # 旧格式: output.text
        if "text" in output:
            return output["text"]

        return "无法解析API响应"

    def _log_usage(self, result: dict, model: ModelType = None, timer: Timer = None):
        """记录 token 用量（结构化日志）"""
        usage = result.get("usage", {})
        if usage:
            log_data = {
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            }
            if model:
                log_data["model"] = model.value
            if timer:
                log_data["duration_ms"] = timer.elapsed_ms()
            logger.info("LLM 调用完成", **log_data)

    # --------------------------------------------------------
    # 对外接口
    # --------------------------------------------------------

    def chat_with_messages(
        self,
        messages: List[dict],
        model: ModelType = ModelType.TURBO,
        **kwargs
    ) -> str:
        """
        用 messages 格式调用（推荐）。

        这是最灵活的方式，你可以完全控制对话历史。
        配合 PromptBuilder 使用效果最好。
        """
        result = self._call_api(messages, model, **kwargs)
        return self._parse_response(result)

    def chat(
        self,
        prompt: str,
        model: ModelType = ModelType.TURBO,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        简单调用（兼容旧代码）。

        内部会把 prompt 包装成 messages 格式。
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return self.chat_with_messages(messages, model, **kwargs)

    # --------------------------------------------------------
    # 知识点7: 流式输出 (Streaming)
    # --------------------------------------------------------
    # 普通调用：等 AI 生成完所有内容，一次性返回（可能等5-10秒）
    # 流式调用：AI 每生成几个字就立刻返回，用户能看到"打字效果"
    #
    # 原理：HTTP SSE (Server-Sent Events)
    # 服务端不断发送小块数据，客户端逐块接收。
    #
    # DashScope 流式调用需要设置:
    # - Header: X-DashScope-SSE: enable
    # - parameters.incremental_output: true

    def chat_stream(
        self,
        prompt: str,
        model: ModelType = ModelType.TURBO,
        system_prompt: Optional[str] = None,
    ) -> Generator[str, None, None]:
        """
        流式调用，逐块返回文本。

        使用方式：
            for chunk in client.chat_stream("讲个故事"):
                print(chunk, end="", flush=True)
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-SSE": "enable",  # 开启流式
        }

        payload = self._build_payload(messages, model)
        payload["parameters"]["incremental_output"] = True  # 增量输出
        timer = Timer()

        try:
            resp = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=60,
                stream=True  # requests 库的流式模式
            )

            # 逐行读取 SSE 数据
            for line in resp.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data:"):
                    continue
                data_str = line[len("data:"):].strip()
                if not data_str:
                    continue
                try:
                    data = json.loads(data_str)
                    text = self._parse_response(data)
                    if text and not text.startswith("[错误]"):
                        yield text
                except json.JSONDecodeError:
                    continue

            logger.info("流式调用完成", model=model.value, duration_ms=timer.elapsed_ms())

        except Exception as e:
            logger.error("流式调用失败", model=model.value, error=str(e))
            yield f"[流式调用错误] {e}"

    def chat_stream_with_messages(
        self,
        messages: List[dict],
        model: ModelType = ModelType.TURBO,
    ) -> Generator[str, None, None]:
        """用 messages 格式流式调用（供 Agent 使用）"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-SSE": "enable",
        }

        payload = self._build_payload(messages, model)
        payload["parameters"]["incremental_output"] = True
        timer = Timer()

        try:
            resp = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=60,
                stream=True
            )

            for line in resp.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data:"):
                    continue
                data_str = line[len("data:"):].strip()
                if not data_str:
                    continue
                try:
                    data = json.loads(data_str)
                    text = self._parse_response(data)
                    if text and not text.startswith("[错误]"):
                        yield text
                except json.JSONDecodeError:
                    continue

            logger.info("流式调用完成", model=model.value, duration_ms=timer.elapsed_ms())

        except Exception as e:
            logger.error("流式调用失败", model=model.value, error=str(e))
            yield f"[流式调用错误] {e}"

    def get_stats(self) -> dict:
        """获取调用统计"""
        return {
            "total_calls": self.total_calls,
            "total_errors": self.total_errors,
            "error_rate": f"{self.total_errors/max(self.total_calls,1)*100:.1f}%"
        }


# ============================================================
# 全局实例 + 兼容旧代码的函数
# ============================================================
# 创建一个全局的 LLMClient 实例，整个应用共享。
# 同时保留 call_qwen() 函数，让旧代码不用改也能跑。

_client = LLMClient()


def call_qwen(prompt: str) -> str:
    """兼容旧代码的简单调用"""
    return _client.chat(prompt)


def get_llm_client() -> LLMClient:
    """获取全局 LLM 客户端实例"""
    return _client
