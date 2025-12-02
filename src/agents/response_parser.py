"""
Shared response parsing utilities for all agents.
Parses structured LLM responses into standardized format.
"""


def parse_choice(response: str, max_options: int) -> int:
    """
    Parse CHOICE from LLM response.

    Args:
        response: LLM response text
        max_options: Maximum number of options

    Returns:
        0-indexed choice (defaults to 0)
    """
    for line in response.split('\n'):
        if line.strip().startswith('CHOICE:'):
            try:
                num = int(line.split(':')[1].strip())
                return max(0, min(num - 1, max_options - 1))
            except ValueError:
                pass
    return 0


def parse_score(response: str) -> int:
    """
    Parse SCORE from LLM response.

    Args:
        response: LLM response text

    Returns:
        Score 0-100 (defaults to 75)
    """
    for line in response.split('\n'):
        if line.strip().startswith('SCORE:'):
            try:
                num = int(line.split(':')[1].strip())
                return max(0, min(num, 100))
            except ValueError:
                pass
    return 75


def parse_reasoning(response: str) -> str:
    """
    Parse REASONING from LLM response.

    Args:
        response: LLM response text

    Returns:
        Reasoning text (defaults to "No reasoning provided")
    """
    for line in response.split('\n'):
        if line.strip().startswith('REASONING:'):
            return line.split(':', 1)[1].strip()
    return "No reasoning provided"


def parse_multiline_reasoning(response: str) -> str:
    """
    Parse REASONING from LLM response, supporting multiple lines.

    Args:
        response: LLM response text

    Returns:
        Reasoning text (may span multiple lines)
    """
    lines = response.split('\n')
    for i, line in enumerate(lines):
        if line.strip().startswith('REASONING:'):
            # Get the reasoning (may span multiple lines)
            reasoning_parts = [line.split(':', 1)[1].strip()]
            # Collect subsequent lines that are part of reasoning
            for j in range(i + 1, len(lines)):
                if lines[j].strip() and not lines[j].strip().startswith(('CHOICE:', 'SCORE:')):
                    reasoning_parts.append(lines[j].strip())
                elif lines[j].strip().startswith(('CHOICE:', 'SCORE:')):
                    break
            return ' '.join(reasoning_parts)
    return "No reasoning provided"
