"""Local demo skills for teaching how reusable AI capabilities are organized."""
from dataclasses import dataclass
from typing import Callable, Dict, List


PROJECT_FILE_MAP = {
    "app": "backend/app_skill04/app.py",
    "routes": "backend/app_skill04/routes.py",
    "agent": "backend/app_skill04/agent.py",
    "prompts": "backend/app_skill04/prompts.py",
    "llm": "backend/app_skill04/llm.py",
    "schemas": "backend/app_skill04/schemas.py",
}


@dataclass
class SkillResult:
    name: str
    summary: str
    core_knowledge: List[str]
    example: str
    related_files: List[str]


@dataclass
class SkillDefinition:
    name: str
    purpose: str
    when_to_use: str
    handler: Callable[[str, str], SkillResult]


def _skill_explain_rag(question: str, context: str) -> SkillResult:
    summary = (
        "This skill explains how your current app turns a user question into a "
        "retrieval-augmented answer. It focuses on the control flow already used "
        "inside app_skill04."
    )
    example = (
        "Example: ask 'What happens after /api/chat receives my question?'. "
        "The skill will point to routes.py -> agent.py -> rag_manager.py -> llm.py."
    )
    core_knowledge = [
        "A skill is a reusable ability with a clear boundary, input, and output.",
        "In your project, the RAG flow is a good candidate for a skill because it is repeatable.",
        "The route receives the request, the agent orchestrates steps, RAG fetches context, and the LLM writes the answer.",
        "Good skills are narrow enough to test and broad enough to reuse.",
    ]
    if question:
        example = f"Example based on your question: '{question}'. Follow the path routes -> agent -> prompts/llm."
    return SkillResult(
        name="explain_rag_flow",
        summary=summary,
        core_knowledge=core_knowledge,
        example=example,
        related_files=[
            PROJECT_FILE_MAP["routes"],
            PROJECT_FILE_MAP["agent"],
            PROJECT_FILE_MAP["prompts"],
            PROJECT_FILE_MAP["llm"],
        ],
    )


def _skill_compare_skill_and_mcp(question: str, context: str) -> SkillResult:
    summary = (
        "This skill compares 'skill' and 'MCP' using the current codebase. "
        "A skill is usually a packaged capability, while MCP is a protocol for "
        "connecting a model runtime to external tools and resources."
    )
    example = (
        "Example: your local 'RAG explainer' is a skill. A server exposing "
        "documents, tools, or knowledge through a standard interface is closer to MCP."
    )
    core_knowledge = [
        "Skill answers 'what capability do I want to package and reuse?'",
        "MCP answers 'how does the model discover and call external context/tools in a standard way?'",
        "You can implement a skill with plain Python functions first; that is the simplest learning path.",
        "Later, the same capability can be exposed through an MCP server so other agents or apps can call it.",
    ]
    if context:
        example = f"Example context: {context}"
    return SkillResult(
        name="compare_skill_and_mcp",
        summary=summary,
        core_knowledge=core_knowledge,
        example=example,
        related_files=[
            PROJECT_FILE_MAP["agent"],
            PROJECT_FILE_MAP["routes"],
        ],
    )


def _skill_generate_learning_path(question: str, context: str) -> SkillResult:
    summary = (
        "This skill generates a beginner-friendly learning path from your current project."
    )
    example = (
        "Step 1: understand prompt/messages and route flow. "
        "Step 2: understand agent orchestration and retrieval. "
        "Step 3: understand skill packaging. "
        "Step 4: understand MCP resources/tools."
    )
    core_knowledge = [
        "Do not start with every framework at once; start from request -> orchestration -> model call.",
        "A prompt is not the whole system. The full system also includes memory, tools, retrieval, and control flow.",
        "Skills and MCP sit above the raw model call and help structure larger applications.",
        "Your app_skill04 folder is a good sandbox because it already has route, prompt, LLM, and agent layers.",
    ]
    if question:
        example = f"Suggested path for '{question}': messages -> prompt -> route -> agent -> skill -> MCP."
    return SkillResult(
        name="generate_learning_path",
        summary=summary,
        core_knowledge=core_knowledge,
        example=example,
        related_files=list(PROJECT_FILE_MAP.values()),
    )


class SkillRegistry:
    """Minimal local skill registry used for teaching."""

    def __init__(self):
        self._skills: Dict[str, SkillDefinition] = {
            "explain_rag_flow": SkillDefinition(
                name="explain_rag_flow",
                purpose="Explain the current RAG execution path in app_skill04.",
                when_to_use="Use when you want to understand the current project structure.",
                handler=_skill_explain_rag,
            ),
            "compare_skill_and_mcp": SkillDefinition(
                name="compare_skill_and_mcp",
                purpose="Explain the conceptual difference between skills and MCP.",
                when_to_use="Use when the two ideas feel similar and you want a concrete comparison.",
                handler=_skill_compare_skill_and_mcp,
            ),
            "generate_learning_path": SkillDefinition(
                name="generate_learning_path",
                purpose="Build a staged study path based on the current codebase.",
                when_to_use="Use when you want to learn the stack gradually as a beginner.",
                handler=_skill_generate_learning_path,
            ),
        }

    def list_skills(self) -> List[dict]:
        return [
            {
                "name": skill.name,
                "purpose": skill.purpose,
                "when_to_use": skill.when_to_use,
            }
            for skill in self._skills.values()
        ]

    def run(self, skill_name: str, question: str = "", context: str = "") -> dict:
        skill = self._skills.get(skill_name)
        if skill is None:
            return {
                "success": False,
                "error": f"Unknown skill: {skill_name}",
                "available_skills": list(self._skills.keys()),
            }

        result = skill.handler(question, context)
        return {
            "success": True,
            "skill": result.name,
            "summary": result.summary,
            "core_knowledge": result.core_knowledge,
            "example": result.example,
            "related_files": result.related_files,
        }


skill_registry = SkillRegistry()
