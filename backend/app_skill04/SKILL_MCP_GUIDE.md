# app_skill04: Skills and MCP Guide

This guide turns the current `app_skill04` folder into a beginner-friendly learning sandbox.

## 1. Read the current app in layers

Start with these files:

- `backend/app_skill04/routes.py`
- `backend/app_skill04/agent.py`
- `backend/app_skill04/prompts.py`
- `backend/app_skill04/llm.py`
- `backend/app_skill04/rag_manager.py`

Suggested reading order:

1. `routes.py`: where HTTP requests enter the system.
2. `agent.py`: where the app decides the execution flow.
3. `prompts.py`: how instructions are assembled for the model.
4. `llm.py`: how the app calls the model API.
5. `rag_manager.py`: how the app reads external knowledge.

## 2. What is a skill

A skill is a packaged capability.

In practice, a skill usually has:

- a purpose
- trigger conditions
- input fields
- output format
- implementation code

In this folder, the file `backend/app_skill04/skills.py` shows a very small local skill registry.

That registry is intentionally simple:

- list available skills
- run one skill by name
- return structured output

This is useful because beginners often put everything into one giant prompt. Skills help you split behavior into clear reusable parts.

## 3. What is MCP

MCP is about standardizing access to external context and actions.

A useful mental model:

- skill = "what capability is packaged"
- MCP = "how capabilities/resources are exposed in a standard way"

The demo in `backend/app_skill04/mcp_demo.py` includes:

- resources: readable pieces of context
- tools: callable actions
- a tiny client flow that reads a resource and calls tools

This is not a full production MCP stack. It is a teaching version designed to make the core protocol ideas concrete.

## 4. How this connects to your current RAG app

Your existing app already has the right building blocks:

- `routes.py` is the app boundary
- `agent.py` is the orchestrator
- `rag_manager.py` is an external knowledge bridge
- `llm.py` is the model client
- `prompts.py` is instruction composition

Skills and MCP sit above or beside these parts:

- skill: package a reusable reasoning or helper ability
- MCP: expose knowledge/tools in a more portable way

## 5. Endpoints to try

### Learning overview

`GET /api/learn/overview`

### Skill concepts and available local skills

`GET /api/learn/skills`

### Run one local skill

`POST /api/learn/skills/run`

Example body:

```json
{
  "skill_name": "compare_skill_and_mcp",
  "question": "我应该先学 skills 还是先学 MCP？",
  "context": "我是大模型初学者"
}
```

### MCP concepts and demo surface

`GET /api/learn/mcp`

### Run the simulated MCP flow

`POST /api/learn/mcp/demo`

Example body:

```json
{
  "question": "我想理解 rag 和 mcp 的关系",
  "resource_uri": "project://concepts/mcp"
}
```

## 6. Recommended study path for you

Because you said you are still new to large models, this order will feel much more natural:

1. Understand `messages`, `prompt`, and `route`.
2. Understand `agent` and `RAG`.
3. Understand why people create `skills`.
4. Understand why people need `MCP`.
5. Then connect them together.

## 7. One sentence summary

If the raw model call is the engine, then skills are reusable driving techniques, and MCP is the standard road interface that lets many tools and knowledge sources plug into the same car.
