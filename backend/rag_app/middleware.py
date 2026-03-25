"""
请求追踪中间件 (Request Tracing Middleware)

核心知识点：
1. FastAPI 中间件 — 拦截每个请求，在处理前后执行自定义逻辑
2. Request ID — 为每个请求生成唯一标识，贯穿整个处理链路
3. 性能监控 — 记录每个请求的处理耗时
4. 响应头注入 — 把 Request ID 返回给客户端，方便调试

中间件的执行顺序（洋葱模型）：
    请求进来 → 中间件A前 → 中间件B前 → 路由处理 → 中间件B后 → 中间件A后 → 响应出去

类比：就像快递站，每个包裹（请求）进来时贴个追踪码（request_id），
      经过分拣（路由）、打包（处理）、出库（响应），全程可追踪。
"""

import uuid
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from .logger import get_logger, set_request_id, Timer

logger = get_logger("middleware")


# ============================================================
# 知识点1: 生成 Request ID
# ============================================================
# UUID4 是随机生成的，碰撞概率极低（约 2^122 分之一）。
# 完整 UUID 太长（36字符），取前8位就够用了（日志更紧凑）。
#
# 也可以用其他方案：
# - 雪花算法 (Snowflake): 有序、可排序，适合分布式系统
# - ULID: 有序 + 随机，比 UUID 更适合做数据库主键
# - 自增ID: 最简单，但不适合分布式

def generate_request_id() -> str:
    """生成短格式的请求追踪 ID"""
    return uuid.uuid4().hex[:8]  # 例如: "a1b2c3d4"


# ============================================================
# 知识点2: FastAPI/Starlette 中间件
# ============================================================
# BaseHTTPMiddleware 是 Starlette 提供的中间件基类。
# 只需要实现 dispatch 方法：
#   async def dispatch(self, request, call_next):
#       # 请求前的逻辑
#       response = await call_next(request)  # 调用下一个中间件或路由
#       # 请求后的逻辑
#       return response
#
# 注意：中间件会拦截所有请求，包括静态文件、健康检查等。
# 如果某些路径不需要追踪，可以在 dispatch 中跳过。

class RequestTraceMiddleware(BaseHTTPMiddleware):
    """请求追踪中间件

    功能：
    1. 为每个请求生成唯一 request_id
    2. 将 request_id 存入 contextvars（整个请求链路可访问）
    3. 记录请求开始和完成的日志（含耗时）
    4. 在响应头中返回 X-Request-ID

    日志输出示例：
        {"request_id": "a1b2c3d4", "message": "请求开始", "method": "POST", "path": "/api/chat"}
        {"request_id": "a1b2c3d4", "message": "请求完成", "status": 200, "duration_ms": 1200}
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # 1. 生成 request_id
        #    优先使用客户端传入的（方便跨服务追踪），否则自动生成
        request_id = request.headers.get("X-Request-ID") or generate_request_id()

        # 2. 存入 contextvars — 这是关键！
        #    之后 agent.py、llm.py、rag_manager.py 中的 logger
        #    都能通过 get_request_id() 自动拿到这个值
        set_request_id(request_id)

        # 3. 记录请求开始
        timer = Timer()
        logger.info(
            "请求开始",
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else "-",
        )

        # 4. 调用下一个中间件或路由处理器
        try:
            response = await call_next(request)
        except Exception as e:
            # 未捕获的异常（理论上 FastAPI 会先捕获，这里是兜底）
            duration = timer.elapsed_ms()
            logger.error(
                "请求异常",
                method=request.method,
                path=request.url.path,
                duration_ms=duration,
                error=str(e),
                exc_info=True,
            )
            raise

        # 5. 记录请求完成
        duration = timer.elapsed_ms()
        log_method = logger.warning if response.status_code >= 400 else logger.info
        log_method(
            "请求完成",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=duration,
        )

        # 6. 在响应头中返回 request_id
        #    前端可以用这个值来反馈问题："我的请求 ID 是 a1b2c3d4，报错了"
        #    运维可以用这个值在日志系统中搜索完整链路
        response.headers["X-Request-ID"] = request_id

        return response
