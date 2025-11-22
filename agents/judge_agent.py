"""
Judge Agent - Evaluates and selects the best content from all agents.
"""

from typing import Dict, Any, List
from agents.base_agent import BaseAgent, AgentTask
from services.claude_client import ClaudeClient
from utils.queue_manager import AgentResult


class JudgeAgent(BaseAgent):
    """
    Agent responsible for judging and selecting the best content.
    Receives results from Video, Song, and Story agents and makes final decision.
    """

    def __init__(self, claude_client: ClaudeClient):
        """
        Initialize Judge Agent.

        Args:
            claude_client: Claude API client
        """
        super().__init__(name="JudgeAgent", agent_type="judge")
        self.claude = claude_client

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
        options = []

        if 'video' in content_results and not content_results['video'].error:
            video_content = content_results['video'].content
            if 'selected' in video_content:
                options.append({
                    'type': 'video',
                    'data': video_content['selected']
                })

        if 'song' in content_results and not content_results['song'].error:
            song_content = content_results['song'].content
            if 'selected' in song_content:
                options.append({
                    'type': 'song',
                    'data': song_content['selected']
                })

        if 'story' in content_results and not content_results['story'].error:
            story_content = content_results['story'].content
            if 'selected' in story_content:
                options.append({
                    'type': 'story',
                    'data': story_content['selected']
                })

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

    def _make_judgment(
        self,
        location: str,
        options: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Use Claude to judge and select the best content option.

        Args:
            location: Location name
            options: List of content options (video, song, story)

        Returns:
            Judgment dictionary with type, data, reasoning, score
        """
        # Build options description
        options_text = []
        for i, opt in enumerate(options):
            opt_type = opt['type']
            data = opt['data']

            if opt_type == 'video':
                desc = f"Video: \"{data.get('title', 'N/A')}\"\n"
                desc += f"  Description: {data.get('description', 'N/A')}\n"
                desc += f"  Duration: {data.get('duration', 'N/A')}\n"
                desc += f"  Channel: {data.get('channel', 'N/A')}"

            elif opt_type == 'song':
                desc = f"Song: \"{data.get('title', 'N/A')}\" by {data.get('artist', 'N/A')}\n"
                desc += f"  Genre: {data.get('genre', 'N/A')}\n"
                desc += f"  Duration: {data.get('duration', 'N/A')}\n"
                desc += f"  Album: {data.get('album', 'N/A')}"

            else:  # story
                desc = f"Story: \"{data.get('title', 'N/A')}\"\n"
                desc += f"  Content: {data.get('content', 'N/A')}\n"
                desc += f"  Category: {data.get('category', 'N/A')}\n"
                desc += f"  Period: {data.get('period', 'N/A')}"

            options_text.append(f"Option {i+1} ({opt_type.upper()}):\n{desc}")

        options_str = "\n\n".join(options_text)

        system_prompt = """You are an expert travel experience designer. Your task is to select the most engaging and appropriate content for a specific location on a traveler's route.

Consider:
- Engagement value: How captivating is the content?
- Relevance: How well does it represent the location?
- Educational value: What will the traveler learn?
- Emotional impact: Will it enhance the travel experience?
- Practicality: Is it consumable during a journey?"""

        user_prompt = f"""Location: {location}

Available content options:
{options_str}

Select the BEST option for this location.

Respond with:
CHOICE: [number 1-{len(options)}]
SCORE: [confidence score 0-100]
REASONING: [detailed explanation of why this is the best choice]"""

        try:
            response = self.claude.simple_query(
                prompt=user_prompt,
                system=system_prompt,
                temperature=0.4
            )

            # Parse response
            choice_idx = self._parse_choice(response, len(options))
            score = self._parse_score(response)
            reasoning = self._parse_reasoning(response)

            chosen_option = options[choice_idx]

            return {
                'type': chosen_option['type'],
                'data': chosen_option['data'],
                'reasoning': reasoning,
                'score': score
            }

        except Exception as e:
            self.logger.warning(f"Claude judgment failed, using first option: {e}")
            return {
                'type': options[0]['type'],
                'data': options[0]['data'],
                'reasoning': "Default selection (Claude unavailable)",
                'score': 50
            }

    def _parse_choice(self, response: str, max_options: int) -> int:
        """Parse CHOICE from Claude response."""
        for line in response.split('\n'):
            if line.strip().startswith('CHOICE:'):
                try:
                    num = int(line.split(':')[1].strip())
                    return max(0, min(num - 1, max_options - 1))
                except ValueError:
                    pass
        return 0

    def _parse_score(self, response: str) -> int:
        """Parse SCORE from Claude response."""
        for line in response.split('\n'):
            if line.strip().startswith('SCORE:'):
                try:
                    score = int(line.split(':')[1].strip())
                    return max(0, min(score, 100))
                except ValueError:
                    pass
        return 50

    def _parse_reasoning(self, response: str) -> str:
        """Parse REASONING from Claude response."""
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
