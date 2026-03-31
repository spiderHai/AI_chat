# app_skill04：技能与 MCP 入门指南

本指南将当前 `app_skill04` 文件夹改造为适合初学者的学习沙箱。

## 一、分层阅读当前应用

先从这些文件入手：

- `backend/app_skill04/routes.py`
- `backend/app_skill04/agent.py`
- `backend/app_skill04/prompts.py`
- `backend/app_skill04/llm.py`
- `backend/app_skill04/rag_manager.py`

推荐阅读顺序：

1. `routes.py`：HTTP 请求进入系统的入口
2. `agent.py`：应用决定执行流程的核心逻辑
3. `prompts.py`：如何为大模型组装指令提示
4. `llm.py`：应用如何调用模型接口
5. `rag_manager.py`：应用如何读取外部知识

## 二、什么是技能（Skill）

技能是被封装好的能力。

在实际开发中，一个技能通常包含：

- 明确用途
- 触发条件
- 输入字段
- 输出格式
- 实现代码

在本文件夹中，`backend/app_skill04/skills.py` 展示了一个极简的本地技能注册器。

该注册器设计得非常简洁：

- 列出可用技能
- 根据名称运行指定技能
- 返回结构化输出

这一设计很实用，因为初学者常常把所有逻辑写在一个庞大的提示词里。而技能可以帮你把行为拆分成清晰、可复用的模块。

## 三、什么是 MCP

MCP 用于标准化外部上下文与操作能力的调用方式。

一个好理解的类比：

- 技能 = 封装好的“能力本身”
- MCP = 能力/资源对外暴露的“标准化方式”

`backend/app_skill04/mcp_demo.py` 中的示例包含：

- 资源（resource）：可读取的上下文片段
- 工具（tool）：可调用的操作行为
- 一段极简的客户端流程：读取资源并调用工具

这并非完整的生产级 MCP 架构，而是教学用简化版本，用于把核心协议逻辑讲清楚。

## 四、与你现有 RAG 应用的关联

你已有的应用已经具备完整的基础模块：

- `routes.py` 作为应用入口边界
- `agent.py` 作为调度编排器
- `rag_manager.py` 作为外部知识桥梁
- `llm.py` 作为模型调用客户端
- `prompts.py` 负责指令组装

技能与 MCP 是在这些模块之上/之外的扩展：

- 技能：封装可复用的推理或辅助能力
- MCP：以更通用、可移植的方式对外暴露知识与工具

## 五、可测试接口

### 学习概览

`GET /api/learn/overview`

### 技能概念与本地可用技能

`GET /api/learn/skills`

### 运行单个本地技能

`POST /api/learn/skills/run`

请求体示例：

```json
{
  "skill_name": "compare_skill_and_mcp",
  "question": "我应该先学 skills 还是先学 MCP？",
  "context": "我是大模型初学者"
}
```

### MCP 概念与示例说明

`GET /api/learn/mcp`

### 运行模拟 MCP 流程

`POST /api/learn/mcp/demo`

请求体示例：

```json
{
  "question": "我想理解 rag 和 mcp 的关系",
  "resource_uri": "project://concepts/mcp"
}
```

## 六、推荐学习路径

考虑到你是大模型初学者，按这个顺序学习会更自然：

1. 理解 `messages`（消息）、`prompt`（提示词）和 `route`（路由）
2. 理解 `agent`（智能体）与 RAG
3. 理解为什么要设计 `skills`（技能）
4. 理解为什么需要 MCP
5. 最后将所有模块串联起来

## 七、一句话总结

如果把原生模型调用比作发动机，那么技能就是可复用的驾驶技巧，而 MCP 则是标准化的道路接口，让各类工具和知识源都能接入同一台车。
