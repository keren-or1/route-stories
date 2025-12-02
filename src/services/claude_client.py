"""
Claude API client wrapper for agent decision-making.
Provides a simplified interface for Claude API calls.
"""

import anthropic
from typing import List, Dict, Any, Optional
from src.utils.logger import get_logger
from src.services.claude_prompts import create_context_query_prompt, create_decision_prompt
from src.services.claude_parser import parse_decision_response


logger = get_logger("claude_client")


class ClaudeClient:
    """Wrapper for Anthropic Claude API."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-5-20250929",
        max_tokens: int = 4096,
        temperature: float = 0.7
    ):
        """Initialize Claude client."""
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        logger.info(f"ClaudeClient initialized with model: {model}")

    def send_message(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Send a message to Claude and get response."""
        try:
            params = {
                "model": self.model,
                "max_tokens": max_tokens or self.max_tokens,
                "temperature": temperature or self.temperature,
                "messages": messages
            }

            if system:
                params["system"] = system

            response = self.client.messages.create(**params)

            # Extract text from response
            if response.content and len(response.content) > 0:
                return response.content[0].text

            return ""

        except Exception as e:
            logger.error(f"Claude API call failed: {e}")
            raise

    def simple_query(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Send a simple query with a single user message."""
        messages = [{"role": "user", "content": prompt}]
        return self.send_message(messages, system=system, temperature=temperature)

    def analyze_with_context(
        self,
        context: str,
        query: str,
        system: Optional[str] = None
    ) -> str:
        """Analyze a query with given context."""
        prompt = create_context_query_prompt(context, query)
        return self.simple_query(prompt, system=system)

    def structured_decision(
        self,
        options: List[Dict[str, Any]],
        criteria: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Make a structured decision between multiple options."""
        prompt = create_decision_prompt(options, criteria, context)

        try:
            response = self.simple_query(prompt, temperature=0.3)
            return parse_decision_response(response, len(options))
        except Exception as e:
            logger.error(f"Structured decision failed: {e}")
            return {
                "choice": 0,
                "score": 0,
                "reasoning": f"Error in decision making: {e}"
            }
