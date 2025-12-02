"""
Response parsing utilities for Gemini API.
"""

from typing import Dict, Any


def parse_decision_response(response: str, num_options: int) -> Dict[str, Any]:
    """
    Parse structured decision response.

    Args:
        response: Gemini's response text
        num_options: Number of options to validate choice

    Returns:
        Parsed decision dictionary
    """
    result = {
        "choice": 0,
        "score": 50,
        "reasoning": response
    }

    lines = response.split('\n')
    for line in lines:
        line = line.strip()

        if line.startswith('CHOICE:'):
            try:
                choice_num = int(line.split(':')[1].strip())
                # Convert to 0-indexed
                result["choice"] = max(0, min(choice_num - 1, num_options - 1))
            except ValueError:
                pass

        elif line.startswith('SCORE:'):
            try:
                score = int(line.split(':')[1].strip())
                result["score"] = max(0, min(score, 100))
            except ValueError:
                pass

        elif line.startswith('REASONING:'):
            result["reasoning"] = line.split(':', 1)[1].strip()

    return result
