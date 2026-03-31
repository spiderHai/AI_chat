"""
提示词管理模块 (Prompt Management)

核心知识点：
1. System Prompt（系统提示词）— 定义 AI 的角色和行为边界
2. Prompt Template（提示词模板）— 用变量占位符构建可复用的提示词
3. Few-Shot Prompting（少样本提示）— 给 AI 几个示例，让它学会输出格式
4. Chain of Thought（思维链）— 引导 AI 分步骤推理
5. Prompt Composition（提示词组合）— 把多个片段拼装成完整提示词
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


# ============================================================
# 知识点1: System Prompt（系统提示词）
# ============================================================
# System Prompt 是发给大模型的第一条消息，role="system"
# 它定义了 AI 的"人设"：你是谁、你该怎么做、你不该做什么
# 大模型会在整个对话中遵守这个设定
#
# 好的 System Prompt 应该包含：
# - 角色定义（你是一个...）
# - 能力边界（你只回答...相关的问题）
# - 输出格式要求（用中文回答、用JSON格式等）
# - 行为约束（不要编造信息、不确定时说不知道）

SYSTEM_PROMPTS = {
    # RAG 问答场景：强调"基于文档回答"，防止 AI 编造
    "rag_qa": (
        "你是一个专业的知识库助手。"
        "你只能基于提供的文档内容回答问题。"
        "如果文档中没有相关信息，请诚实说'根据现有资料，我没有找到相关信息'。"
        "不要编造任何文档中不存在的内容。"
        "用中文回答，语气友好专业。"
    ),

    # 分析场景：要求结构化输出
    "analyzer": (
        "你是一个问题分析助手。"
        "分析用户的问题意图，判断需要什么信息来回答。"
        "必须以JSON格式响应: {\"thinking\": \"分析过程\", \"need_more_info\": bool}"
    ),

    # 通用聊天：宽松一些
    "general": (
        "你是一个友好的AI助手，用中文回答问题。"
        "回答要简洁、准确、有帮助。"
    ),
}


# ============================================================
# 知识点2: Prompt Template（提示词模板）
# ============================================================
# 为什么需要模板？因为提示词的"骨架"是固定的，只有部分内容是动态的。
# 比如 RAG 场景，骨架永远是"这是文档内容:...，问题是:...，请回答"
# 变化的只是具体的文档和问题。
#
# 用 dataclass 而不是纯字符串，好处是：
# - 有类型检查，少传参数会报错
# - 可以设默认值
# - 代码可读性好

@dataclass
class PromptTemplate:
    """提示词模板基类"""
    template: str           # 模板字符串，用 {变量名} 占位
    required_vars: List[str] = field(default_factory=list)  # 必填变量

    def render(self, **kwargs) -> str:
        """渲染模板，把变量替换进去"""
        # 检查必填变量
        missing = [v for v in self.required_vars if v not in kwargs]
        if missing:
            raise ValueError(f"缺少必填变量: {missing}")
        return self.template.format(**kwargs)


# RAG 问答模板
RAG_ANSWER_TEMPLATE = PromptTemplate(
    template=(
        "用户问题: {question}\n\n"
        "以下是从知识库中检索到的相关文档内容:\n"
        "---\n"
        "{context}\n"
        "---\n\n"
        "请基于以上文档内容回答用户问题。"
    ),
    required_vars=["question", "context"]
)

# 分析模板
ANALYZE_TEMPLATE = PromptTemplate(
    template=(
        "用户问题: {question}\n\n"
        "检索到的相关信息:\n{context}\n\n"
        "请分析这个问题，以JSON格式响应:\n"
        '{{\"thinking\": \"你的分析过程\", \"need_more_info\": false}}'
    ),
    required_vars=["question", "context"]
)


# ============================================================
# 知识点3: Few-Shot Prompting（少样本提示）
# ============================================================
# 有时候光靠指令描述，AI 还是不太理解你要什么格式。
# 这时候给它几个"示例"（example），它就能模仿着来。
#
# 原理：大模型的核心能力是"模式匹配"，
# 你给它看几个 输入→输出 的例子，它就学会了这个模式。
#
# 注意：示例不是越多越好，通常 2-3 个就够了，太多会浪费 token。

@dataclass
class FewShotExample:
    """一个少样本示例"""
    user_input: str     # 用户输入
    ai_output: str      # 期望的 AI 输出


# RAG 场景的少样本示例
RAG_FEW_SHOT_EXAMPLES = [
    FewShotExample(
        user_input="你们的基础版多少钱？",
        ai_output="根据文档信息，基础版价格为 ¥99/月，包含1000次对话/月、基础知识库功能和邮件支持。"
    ),
    FewShotExample(
        user_input="你们支持私有化部署吗？",
        ai_output="是的，我们支持私有化部署。企业版提供私有化部署方案，价格为定制价格，同时还包含无限对话次数、专属客户经理和SLA保障。"
    ),
]


def build_few_shot_prompt(examples: List[FewShotExample]) -> str:
    """把少样本示例拼成提示词片段"""
    lines = ["以下是一些回答示例:\n"]
    for i, ex in enumerate(examples, 1):
        lines.append(f"示例{i}:")
        lines.append(f"  问: {ex.user_input}")
        lines.append(f"  答: {ex.ai_output}\n")
    return "\n".join(lines)


# ============================================================
# 知识点4: Prompt Composition（提示词组合器）
# ============================================================
# 实际项目中，一个完整的提示词往往由多个部分组成：
#   System Prompt + Few-Shot 示例 + 检索到的上下文 + 用户问题
#
# PromptBuilder 就是把这些零件按顺序拼装起来。
# 这样每个部分可以独立修改，不会互相影响。

class PromptBuilder:
    """提示词组合器 — 把多个片段拼装成完整的 messages 列表"""

    def __init__(self):
        self.system_prompt: Optional[str] = None
        self.few_shot_examples: List[FewShotExample] = []
        self.context: Optional[str] = None
        self.user_message: Optional[str] = None

    def set_system(self, prompt_key: str) -> "PromptBuilder":
        """设置系统提示词（从预定义的 SYSTEM_PROMPTS 中选）"""
        self.system_prompt = SYSTEM_PROMPTS.get(prompt_key, SYSTEM_PROMPTS["general"])
        return self  # 返回 self 支持链式调用

    def set_few_shot(self, examples: List[FewShotExample]) -> "PromptBuilder":
        """添加少样本示例"""
        self.few_shot_examples = examples
        return self

    def set_context(self, context: str) -> "PromptBuilder":
        """设置 RAG 检索到的上下文"""
        self.context = context
        return self

    def set_user_message(self, message: str) -> "PromptBuilder":
        """设置用户消息"""
        self.user_message = message
        return self

    def build_messages(self) -> List[dict]:
        """
        构建最终的 messages 列表，这就是发给大模型 API 的格式。

        大模型 API 接收的 messages 格式：
        [
            {"role": "system", "content": "系统提示词"},
            {"role": "user", "content": "示例问题1"},
            {"role": "assistant", "content": "示例回答1"},
            {"role": "user", "content": "实际问题"}
        ]

        role 有三种：
        - system: 系统指令，AI 会始终遵守
        - user: 用户说的话
        - assistant: AI 之前的回复（用于上下文或 few-shot）
        """
        messages = []

        # 1. System Prompt（最重要，放最前面）
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})

        # 2. Few-Shot 示例（模拟之前的对话）
        for ex in self.few_shot_examples:
            messages.append({"role": "user", "content": ex.user_input})
            messages.append({"role": "assistant", "content": ex.ai_output})

        # 3. 用户实际问题（带上 RAG 上下文）
        if self.user_message:
            if self.context:
                content = RAG_ANSWER_TEMPLATE.render(
                    question=self.user_message,
                    context=self.context
                )
            else:
                content = self.user_message
            messages.append({"role": "user", "content": content})

        return messages

    def build_single_prompt(self) -> str:
        """构建单字符串提示词（用于不支持 messages 格式的场景）"""
        parts = []
        if self.system_prompt:
            parts.append(f"[系统指令] {self.system_prompt}")
        if self.few_shot_examples:
            parts.append(build_few_shot_prompt(self.few_shot_examples))
        if self.context:
            parts.append(f"[参考文档]\n{self.context}")
        if self.user_message:
            parts.append(f"[用户问题] {self.user_message}")
        return "\n\n".join(parts)
