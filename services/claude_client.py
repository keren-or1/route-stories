"""
Claude API client wrapper for agent decision-making.
Provides a simplified interface for Claude API calls.
"""

import anthropic
from typing import List, Dict, Any, Optional
from utils.logger import get_logger


logger = get_logger("claude_client")


class ClaudeClient:
    """
    Wrapper for Anthropic Claude API.
    Handles API calls with proper error handling and retries.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-5-20250929",
        max_tokens: int = 4096,
        temperature: float = 0.7
    ):
        """
        Initialize Claude client.

        Args:
            api_key: Anthropic API key
            model: Claude model identifier
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0-1.0)
        """
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
        """
        Send a message to Claude and get response.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            system: Optional system prompt
            temperature: Override default temperature
            max_tokens: Override default max_tokens

        Returns:
            Response text from Claude

        Raises:
            Exception: If API call fails
        """
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
        """
        Send a simple query with a single user message.

        Args:
            prompt: User prompt text
            system: Optional system prompt
            temperature: Override default temperature

        Returns:
            Response text from Claude
        """
        messages = [{"role": "user", "content": prompt}]
        return self.send_message(messages, system=system, temperature=temperature)

    def analyze_with_context(
        self,
        context: str,
        query: str,
        system: Optional[str] = None
    ) -> str:
        """
        Analyze a query with given context.

        Args:
            context: Contextual information
            query: Question or task
            system: Optional system prompt

        Returns:
            Response text from Claude
        """
        prompt = f"""Context:
{context}

Query:
{query}

Please provide a detailed response based on the context above."""

        return self.simple_query(prompt, system=system)

    def structured_decision(
        self,
        options: List[Dict[str, Any]],
        criteria: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Make a structured decision between multiple options.

        Args:
            options: List of option dictionaries
            criteria: Decision criteria
            context: Optional additional context

        Returns:
            Dictionary with 'choice' (index), 'reasoning', and 'score'
        """
        options_text = "\n\n".join([
            f"Option {i+1}:\n{self._format_dict(opt)}"
            for i, opt in enumerate(options)
        ])

        context_text = f"\n\nAdditional Context:\n{context}" if context else ""

        prompt = f"""You are a decision-making assistant. Analyze the following options and choose the best one based on the criteria.

{options_text}{context_text}

Criteria for decision:
{criteria}

Please respond in the following format:
CHOICE: [number of chosen option, 1-{len(options)}]
SCORE: [confidence score 0-100]
REASONING: [brief explanation of why this option is best]
"""

        try:
            response = self.simple_query(prompt, temperature=0.3)
            return self._parse_decision_response(response, len(options))
        except Exception as e:
            logger.error(f"Structured decision failed: {e}")
            # Fallback: return first option
            return {
                "choice": 0,
                "score": 0,
                "reasoning": f"Error in decision making: {e}"
            }

    def _format_dict(self, data: Dict[str, Any]) -> str:
        """Format dictionary as readable text."""
        lines = []
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                import json
                value = json.dumps(value, indent=2)
            lines.append(f"{key}: {value}")
        return "\n".join(lines)

    def _parse_decision_response(self, response: str, num_options: int) -> Dict[str, Any]:
        """
        Parse structured decision response.

        Args:
            response: Claude's response text
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
