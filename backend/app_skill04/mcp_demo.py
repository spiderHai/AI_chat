"""A tiny in-process MCP-style demo used for learning."""
from dataclasses import dataclass
from typing import Callable, Dict, List


@dataclass
class MCPResource:
    uri: str
    title: str
    description: str
    content: str


@dataclass
class MCPTool:
    name: str
    description: str
    input_schema: dict
    handler: Callable[[dict], dict]


class DemoMCPServer:
    """A tiny server that exposes resources and tools."""

    def __init__(self):
        self._resources: Dict[str, MCPResource] = {
            "project://architecture/rag_flow": MCPResource(
                uri="project://architecture/rag_flow",
                title="RAG flow in app_skill04",
                description="How the current project moves from route to agent to retrieval to answer.",
                content=(
                    "Flow: routes.py receives /api/chat, then agent.py builds the LangGraph flow. "
                    "The retrieve node gets relevant chunks, the analyze node structures reasoning, "
                    "and the answer node uses prompts.py plus llm.py to produce the final response."
                ),
            ),
            "project://concepts/skills": MCPResource(
                uri="project://concepts/skills",
                title="What is a skill",
                description="A small reusable capability with a clear boundary.",
                content=(
                    "A skill packages know-how. It usually includes: purpose, trigger conditions, "
                    "inputs, outputs, and a concrete implementation. In this project, a local Python "
                    "function can already be treated as a beginner-friendly skill."
                ),
            ),
            "project://concepts/mcp": MCPResource(
                uri="project://concepts/mcp",
                title="What is MCP",
                description="A protocol-oriented way to expose tools and resources to models.",
                content=(
                    "MCP separates the model runtime from external capabilities. A model or agent can "
                    "list resources, read resources, list tools, and call tools through a standard pattern. "
                    "That makes integrations more portable than hard-coding every tool into one app."
                ),
            ),
        }
        self._tools: Dict[str, MCPTool] = {
            "summarize_learning_order": MCPTool(
                name="summarize_learning_order",
                description="Return a beginner-friendly study order.",
                input_schema={"type": "object", "properties": {"topic": {"type": "string"}}},
                handler=self._summarize_learning_order,
            ),
            "map_concept_to_files": MCPTool(
                name="map_concept_to_files",
                description="Map a concept to the most relevant files in app_skill04.",
                input_schema={"type": "object", "properties": {"concept": {"type": "string"}}},
                handler=self._map_concept_to_files,
            ),
        }

    def list_resources(self) -> List[dict]:
        return [
            {
                "uri": resource.uri,
                "title": resource.title,
                "description": resource.description,
            }
            for resource in self._resources.values()
        ]

    def read_resource(self, uri: str) -> dict:
        resource = self._resources.get(uri)
        if resource is None:
            return {"success": False, "error": f"Unknown resource: {uri}"}
        return {
            "success": True,
            "uri": resource.uri,
            "title": resource.title,
            "description": resource.description,
            "content": resource.content,
        }

    def list_tools(self) -> List[dict]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            }
            for tool in self._tools.values()
        ]

    def call_tool(self, name: str, arguments: dict) -> dict:
        tool = self._tools.get(name)
        if tool is None:
            return {"success": False, "error": f"Unknown tool: {name}"}
        result = tool.handler(arguments)
        return {"success": True, "tool": name, "arguments": arguments, "result": result}

    def _summarize_learning_order(self, arguments: dict) -> dict:
        topic = arguments.get("topic", "AI app basics")
        return {
            "topic": topic,
            "steps": [
                "Understand request/response and route handlers.",
                "Understand prompt/messages and model calls.",
                "Understand agent orchestration and state.",
                "Understand retrieval and external knowledge.",
                "Understand skills as packaged capability.",
                "Understand MCP as a standard interface for resources and tools.",
            ],
        }

    def _map_concept_to_files(self, arguments: dict) -> dict:
        concept = arguments.get("concept", "").lower()
        mapping = {
            "route": ["backend/app_skill04/routes.py", "backend/app_skill04/app.py"],
            "agent": ["backend/app_skill04/agent.py", "backend/app_skill04/schemas.py"],
            "prompt": ["backend/app_skill04/prompts.py", "backend/app_skill04/agent.py"],
            "llm": ["backend/app_skill04/llm.py", "backend/app_skill04/prompts.py"],
            "rag": [
                "backend/app_skill04/rag_manager.py",
                "backend/app_skill04/agent.py",
                "backend/app_skill04/routes.py",
            ],
            "skill": ["backend/app_skill04/skills.py", "backend/app_skill04/routes.py"],
            "mcp": ["backend/app_skill04/mcp_demo.py", "backend/app_skill04/routes.py"],
        }
        files = mapping.get(concept, ["backend/app_skill04/routes.py"])
        return {"concept": concept or "default", "files": files}


class DemoMCPClient:
    """A tiny client that shows the mental model of MCP interactions."""

    def __init__(self, server: DemoMCPServer):
        self.server = server

    def demo_learning_flow(self, question: str, resource_uri: str) -> dict:
        resource = self.server.read_resource(resource_uri)
        if not resource.get("success"):
            return resource

        mapped_files = self.server.call_tool(
            "map_concept_to_files",
            {"concept": self._infer_concept(question)},
        )
        study_plan = self.server.call_tool(
            "summarize_learning_order",
            {"topic": question},
        )
        return {
            "success": True,
            "question": question,
            "resource_used": resource,
            "tool_calls": [mapped_files, study_plan],
            "explanation": (
                "This demo mimics an MCP client flow: discover or choose a resource, "
                "read it, then call one or more tools to transform that context into "
                "an answer or a plan."
            ),
        }

    def _infer_concept(self, question: str) -> str:
        lowered = question.lower()
        for candidate in ("mcp", "skill", "rag", "prompt", "agent", "route", "llm"):
            if candidate in lowered:
                return candidate
        return "rag"


demo_mcp_server = DemoMCPServer()
demo_mcp_client = DemoMCPClient(demo_mcp_server)
