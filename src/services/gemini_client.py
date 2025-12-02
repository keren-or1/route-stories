"""
Google Gemini API client wrapper for agent decision-making.
Provides a simplified interface for Gemini API calls.
"""

import time
import google.generativeai as genai
from typing import List, Dict, Any, Optional
from src.utils.logger import get_logger
from src.services.gemini_prompts import create_context_query_prompt, create_decision_prompt
from src.services.gemini_parser import parse_decision_response
from src.services.gemini_retry import RetryHandler


logger = get_logger("gemini_client")


class GeminiClient:
    """
    Wrapper for Google Gemini API.
    Handles API calls with proper error handling and retries.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash-exp",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        retry_delay: float = 1.0,
        max_retries: int = 3
    ):
        """Initialize Gemini client."""
        genai.configure(api_key=api_key)
        self.model_name = model
        self.model = genai.GenerativeModel(model)
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.retry_delay = retry_delay
        self.max_retries = max_retries
        self.retry_handler = RetryHandler(max_retries, retry_delay)
        logger.info(f"GeminiClient initialized with model: {model}")

    def send_message(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Send a message to Gemini and get response."""
        for attempt in range(self.retry_handler.max_retries):
            try:
                # Convert messages to Gemini format
                prompt = ""
                for msg in messages:
                    if msg['role'] == 'user':
                        prompt = msg['content']
                if system:
                    prompt = f"{system}\n\n{prompt}"

                # Generate response
                response = self.model.generate_content(
                    prompt,
                    generation_config={
                        'temperature': temperature or self.temperature,
                        'max_output_tokens': max_tokens or self.max_tokens,
                    }
                )

                return response.text if response.text else ""

            except Exception as e:
                if not self.retry_handler.should_retry(e, attempt):
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

    def _parse_decision_response(self, response: str, num_options: int):
        """Parse decision response (backward compatibility)."""
        return parse_decision_response(response, num_options)

    def _format_dict(self, data):
        """Format dictionary (backward compatibility)."""
        from src.services.gemini_prompts import format_dict
        return format_dict(data)
