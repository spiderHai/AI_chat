"""
结构化日志模块 (Structured Logging)

核心知识点：
1. logging 模块的层级结构 — Logger → Handler → Formatter
2. JSON 格式日志 — 方便对接 ELK/Grafana 等监控系统
3. contextvars — 在异步环境中安全传递请求级别的上下文（如 request_id）
4. 日志级别 — DEBUG < INFO < WARNING < ERROR < CRITICAL

为什么不用 print？
- print 没有级别区分，生产环境无法过滤
- print 没有时间戳、模块名等元信息
- print 无法输出到文件、远程日志系统
- print 在多线程/异步环境下可能交错混乱
"""

import json
import logging
import time
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Optional


# ============================================================
# 知识点1: contextvars — 请求级别的上下文传递
# ============================================================
# 问题：一个 HTTP 请求会经过 中间件 → 路由 → Agent → LLM 多个模块，
#       怎么让所有模块都能拿到同一个 request_id？
#
# 方案1: 函数参数层层传递 → 侵入性太强，每个函数都要加参数
# 方案2: 全局变量 → 多个请求并发时会互相覆盖（线程不安全）
# 方案3: contextvars → Python 3.7+ 提供的"协程本地变量"
#        每个异步任务（协程）有自己独立的一份，互不干扰
#
# 类比：就像 Java 的 ThreadLocal，但支持 asyncio

# 存储当前请求的 request_id，默认值 "-"（表示非请求上下文）
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


def get_request_id() -> str:
    """获取当前请求的 request_id"""
    return request_id_var.get()


def set_request_id(rid: str):
    """设置当前请求的 request_id"""
    request_id_var.set(rid)


# ============================================================
# 知识点2: 自定义 JSON Formatter
# ============================================================
# logging 模块的架构：
#
#   Logger（记录器）
#     ↓ 产生 LogRecord
#   Handler（处理器）— 决定日志去哪里（控制台、文件、网络）
#     ↓
#   Formatter（格式化器）— 决定日志长什么样
#
# 默认 Formatter 输出纯文本，比如：
#   2024-03-19 10:30:00 INFO [llm] LLM调用完成
#
# 我们自定义一个 JSON Formatter，输出：
#   {"timestamp": "...", "level": "INFO", "request_id": "a1b2c3", ...}
#
# JSON 格式的好处：
# - 机器可解析，方便 ELK/Splunk/Grafana 等工具采集
# - 可以携带任意结构化字段（耗时、token数、模型名等）
# - 支持嵌套数据

class JSONFormatter(logging.Formatter):
    """JSON 格式的日志 Formatter

    每条日志输出为一行 JSON，包含：
    - timestamp: ISO 格式时间戳
    - level: 日志级别 (INFO/WARNING/ERROR...)
    - request_id: 当前请求的追踪 ID
    - module: 产生日志的模块名
    - message: 日志消息
    - 其他自定义字段（通过 extra 参数传入）
    """

    def format(self, record: logging.LogRecord) -> str:
        # 基础字段 — 每条日志都有
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "request_id": get_request_id(),  # 从 contextvars 自动获取
            "module": record.name,
            "message": record.getMessage(),
        }

        # 额外字段 — 通过 logger.info("msg", extra={"key": "value"}) 传入
        # 这是结构化日志的精髓：除了消息文本，还能附带任意数据
        if hasattr(record, "extra_data") and record.extra_data:
            log_data.update(record.extra_data)

        # 异常信息 — 如果有异常，附带完整的 traceback
        if record.exc_info and record.exc_info[0] is not None:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


# ============================================================
# 知识点3: 带 extra 数据的 Logger 适配器
# ============================================================
# 标准 logging 的 extra 参数用起来不太方便：
#   logger.info("msg", extra={"extra_data": {"key": "value"}})
#
# 我们封装一个适配器，让调用更自然：
#   logger.info("msg", key="value", duration_ms=100)

class StructuredLogger:
    """结构化日志适配器

    在标准 Logger 基础上，支持直接传入额外字段：
        logger = get_logger("llm")
        logger.info("LLM调用完成", model="qwen-turbo", duration_ms=800)

    输出：
        {"timestamp": "...", "module": "llm", "message": "LLM调用完成",
         "model": "qwen-turbo", "duration_ms": 800}
    """

    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def _log(self, level: int, message: str, **kwargs):
        """内部日志方法，把 kwargs 作为 extra_data 传入"""
        # 创建 LogRecord 时附带 extra_data
        self._logger.log(
            level, message,
            extra={"extra_data": kwargs if kwargs else None}
        )

    def debug(self, message: str, **kwargs):
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """记录错误日志，自动附带异常信息"""
        if "exc_info" not in kwargs:
            # 默认不附带异常栈，除非显式传入 exc_info=True
            self._logger.log(
                logging.ERROR, message,
                extra={"extra_data": kwargs if kwargs else None}
            )
        else:
            exc_info = kwargs.pop("exc_info")
            self._logger.log(
                logging.ERROR, message,
                exc_info=exc_info,
                extra={"extra_data": kwargs if kwargs else None}
            )


# ============================================================
# 知识点4: 日志配置 + 工厂函数
# ============================================================
# 整个应用只需要配置一次日志系统（在模块加载时执行）。
# 之后各模块通过 get_logger("模块名") 获取自己的 logger。
#
# 日志级别说明：
# - DEBUG: 开发调试信息（生产环境通常关闭）
# - INFO: 正常运行信息（请求开始/完成、操作成功）
# - WARNING: 警告（重试、降级、接近限制）
# - ERROR: 错误（请求失败、异常）
# - CRITICAL: 严重错误（系统无法运行）

def _setup_logging():
    """初始化日志系统（只执行一次）"""
    # 获取根 logger
    root_logger = logging.getLogger("rag_app")
    root_logger.setLevel(logging.DEBUG)

    # 避免重复添加 handler（模块可能被多次 import）
    if root_logger.handlers:
        return

    # 控制台 Handler — 输出到 stdout
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # 控制台只显示 INFO 及以上
    console_handler.setFormatter(JSONFormatter())

    root_logger.addHandler(console_handler)

    # 生产环境还可以添加：
    # - FileHandler: 输出到文件（按日期轮转）
    # - 远程 Handler: 发送到 ELK/Loki 等日志系统
    # 示例：
    # file_handler = logging.handlers.RotatingFileHandler(
    #     "app.log", maxBytes=10*1024*1024, backupCount=5
    # )
    # file_handler.setFormatter(JSONFormatter())
    # root_logger.addHandler(file_handler)


# 模块加载时自动初始化
_setup_logging()


def get_logger(name: str) -> StructuredLogger:
    """获取结构化日志实例

    用法：
        from .logger import get_logger
        logger = get_logger("llm")
        logger.info("调用完成", model="qwen-turbo", duration_ms=800)

    参数：
        name: 模块名，会显示在日志的 module 字段中
              建议用文件名，如 "llm", "agent", "routes"
    """
    return StructuredLogger(logging.getLogger(f"rag_app.{name}"))


# ============================================================
# 知识点5: 计时工具
# ============================================================
# 企业级项目中，性能监控非常重要。
# 提供一个简单的计时器，方便记录各阶段耗时。

class Timer:
    """简单计时器，用于记录操作耗时

    用法：
        timer = Timer()
        # ... 执行操作 ...
        logger.info("操作完成", duration_ms=timer.elapsed_ms())

    或者用 with 语句：
        with Timer() as t:
            # ... 执行操作 ...
        logger.info("操作完成", duration_ms=t.elapsed_ms())
    """

    def __init__(self):
        self.start_time = time.perf_counter()

    def elapsed_ms(self) -> int:
        """返回从创建到现在的毫秒数"""
        return int((time.perf_counter() - self.start_time) * 1000)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass
