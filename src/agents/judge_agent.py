"""
Judge Agent - Evaluates and selects the best content from all agents.
"""

from typing import Dict, Any, List
from src.agents.base_agent import BaseAgent, AgentTask
from src.services.gemini_client import GeminiClient
from src.utils.queue_manager import AgentResult
from src.agents.agent_prompts import JudgePrompts
from src.agents.response_parser import parse_choice, parse_score, parse_multiline_reasoning
from src.agents.judge_formatter import format_option_description


class JudgeAgent(BaseAgent):
    """
    Agent responsible for judging and selecting the best content.
    Receives results from Video, Song, and Story agents and makes final decision.
    """

    def __init__(self, gemini_client: GeminiClient):
        """
        Initialize Judge Agent.

        Args:
            gemini_client: Gemini API client
        """
        super().__init__(name="JudgeAgent", agent_type="judge")
        self.gemini = gemini_client

    def execute(self, task: AgentTask) -> AgentResult:
        """
        Judge expects content_results in task.context.

        Args:
            task: AgentTask with content_results in context

        Returns:
            AgentResult with judgment decision
        """
        if not task.context or 'content_results' not in task.context:
            return self._create_result(
                task=task,
                content={},
                error="No content results provided for judging"
            )

        content_results = task.context['content_results']

        self.logger.info(f"Judging content for: {task.address}")

        # Extract the selected items from each agent
        options = self._extract_options(content_results)

        if not options:
            return self._create_result(
                task=task,
                content={},
                error="No valid options to judge"
            )

        # Make judgment
        judgment = self._make_judgment(task.address, options)

        # Create result
        content = {
            "chosen_type": judgment['type'],
            "chosen_content": judgment['data'],
            "reasoning": judgment['reasoning'],
            "score": judgment['score'],
            "all_options": options
        }

        self.logger.info(
            f"Judgment: {judgment['type']} (score: {judgment['score']})"
        )

        return self._create_result(task=task, content=content)

    def _extract_options(self, content_results: Dict[str, AgentResult]) -> List[Dict[str, Any]]:
        """Extract valid content options from agent results."""
        options = []

        for agent_type in ['video', 'song', 'story']:
            if agent_type in content_results and not content_results[agent_type].error:
                content = content_results[agent_type].content
                if 'selected' in content:
                    options.append({
                        'type': agent_type,
                        'data': content['selected']
                    })

        return options

    def _make_judgment(
        self,
        location: str,
        options: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Use Gemini to judge and select the best content option.

        Args:
            location: Location name
            options: List of content options (video, song, story)

        Returns:
            Judgment dictionary with type, data, reasoning, score
        """
        # Build options description
        options_text = []
        for i, opt in enumerate(options):
            desc = format_option_description(opt['type'], opt['data'])
            options_text.append(f"Option {i+1} ({opt['type'].upper()}):\n{desc}")

        options_str = "\n\n".join(options_text)

        # Get prompts
        system_prompt = JudgePrompts.SYSTEM
        user_prompt = JudgePrompts.user_prompt(location, options_str, len(options))

        try:
            response = self.gemini.simple_query(
                prompt=user_prompt,
                system=system_prompt,
                temperature=0.4
            )

            # Parse response
            choice_idx = parse_choice(response, len(options))
            score = parse_score(response)
            reasoning = parse_multiline_reasoning(response)

            chosen_option = options[choice_idx]

            return {
                'type': chosen_option['type'],
                'data': chosen_option['data'],
                'reasoning': reasoning,
                'score': score
            }

        except Exception as e:
            self.logger.warning(f"Gemini judgment failed, using first option: {e}")
            return {
                'type': options[0]['type'],
                'data': options[0]['data'],
                'reasoning': "Default selection (Gemini unavailable)",
                'score': 50
            }
