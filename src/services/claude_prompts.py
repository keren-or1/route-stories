"""
Prompt templates for Claude API interactions.
"""

from typing import List, Dict, Any


def format_dict(data: Dict[str, Any]) -> str:
    """Format dictionary as readable text."""
    lines = []
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            import json
            value = json.dumps(value, indent=2)
        lines.append(f"{key}: {value}")
    return "\n".join(lines)


def create_context_query_prompt(context: str, query: str) -> str:
    """Create a prompt for context-based query."""
    return f"""Context:
{context}

Query:
{query}

Please provide a detailed response based on the context above."""


def create_decision_prompt(
    options: List[Dict[str, Any]],
    criteria: str,
    context: str = None
) -> str:
    """Create a structured decision prompt."""
    options_text = "\n\n".join([
        f"Option {i+1}:\n{format_dict(opt)}"
        for i, opt in enumerate(options)
    ])

    context_text = f"\n\nAdditional Context:\n{context}" if context else ""

    return f"""You are a decision-making assistant. Analyze the following options and choose the best one based on the criteria.

{options_text}{context_text}

Criteria for decision:
{criteria}

Please respond in the following format:
CHOICE: [number of chosen option, 1-{len(options)}]
SCORE: [confidence score 0-100]
REASONING: [brief explanation of why this option is best]
"""
