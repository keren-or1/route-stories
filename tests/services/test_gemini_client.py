"""
Unit tests for GeminiClient.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from src.services.gemini_client import GeminiClient


class TestGeminiClient:
    """Tests for GeminiClient."""

    @patch('src.services.gemini_client.genai')
    def test_init(self, mock_genai):
        """Test client initialization."""
        mock_model = Mock()
        mock_genai.GenerativeModel.return_value = mock_model

        client = GeminiClient(
            api_key="test_api_key",
            model="gemini-2.0-flash-exp",
            max_tokens=2048,
            temperature=0.5
        )

        assert client.model_name == "gemini-2.0-flash-exp"
        assert client.max_tokens == 2048
        assert client.temperature == 0.5
        assert client.retry_delay == 1.0
        assert client.max_retries == 3
        mock_genai.configure.assert_called_once_with(api_key="test_api_key")

    @patch('src.services.gemini_client.genai')
    def test_send_message_success(self, mock_genai):
        """Test successful message sending."""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Test response from Gemini"
        mock_model.generate_content.return_value = mock_response

        mock_genai.GenerativeModel.return_value = mock_model

        client = GeminiClient(api_key="test_key")
        messages = [{"role": "user", "content": "Hello Gemini"}]

        response = client.send_message(messages)

        assert response == "Test response from Gemini"
        mock_model.generate_content.assert_called_once()

    @patch('src.services.gemini_client.genai')
    def test_send_message_with_system_prompt(self, mock_genai):
        """Test message sending with system prompt."""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Response with system context"
        mock_model.generate_content.return_value = mock_response

        mock_genai.GenerativeModel.return_value = mock_model

        client = GeminiClient(api_key="test_key")
        messages = [{"role": "user", "content": "What's 2+2?"}]
        system = "You are a helpful math tutor."

        response = client.send_message(messages, system=system)

        assert response == "Response with system context"
        # Check that system prompt was prepended
        call_args = mock_model.generate_content.call_args
        prompt = call_args[0][0]
        assert "helpful math tutor" in prompt
        assert "What's 2+2?" in prompt

    @patch('src.services.gemini_client.genai')
    def test_send_message_with_temperature_override(self, mock_genai):
        """Test message sending with custom temperature."""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Creative response"
        mock_model.generate_content.return_value = mock_response

        mock_genai.GenerativeModel.return_value = mock_model

        client = GeminiClient(api_key="test_key", temperature=0.5)
        messages = [{"role": "user", "content": "Be creative"}]

        response = client.send_message(messages, temperature=1.0)

        assert response == "Creative response"
        call_args = mock_model.generate_content.call_args
        gen_config = call_args[1]['generation_config']
        assert gen_config['temperature'] == 1.0

    @patch('src.services.gemini_client.genai')
    def test_send_message_empty_response(self, mock_genai):
        """Test handling of empty response."""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = None
        mock_model.generate_content.return_value = mock_response

        mock_genai.GenerativeModel.return_value = mock_model

        client = GeminiClient(api_key="test_key")
        messages = [{"role": "user", "content": "Test"}]

        response = client.send_message(messages)

        assert response == ""

    @patch('src.services.gemini_client.genai')
    @patch('src.services.gemini_client.time.sleep')
    def test_send_message_rate_limit_retry(self, mock_sleep, mock_genai):
        """Test retry logic on rate limit error."""
        mock_model = Mock()

        # First call raises rate limit error, second succeeds
        mock_response = Mock()
        mock_response.text = "Success after retry"
        mock_model.generate_content.side_effect = [
            Exception("429 rate limit exceeded"),
            mock_response
        ]

        mock_genai.GenerativeModel.return_value = mock_model

        client = GeminiClient(api_key="test_key", retry_delay=0.1)
        messages = [{"role": "user", "content": "Test"}]

        response = client.send_message(messages)

        assert response == "Success after retry"
        assert mock_model.generate_content.call_count == 2
        mock_sleep.assert_called_once()

    @patch('src.services.gemini_client.genai')
    @patch('src.services.gemini_client.time.sleep')
    def test_send_message_max_retries_exceeded(self, mock_sleep, mock_genai):
        """Test that exception is raised after max retries."""
        mock_model = Mock()
        mock_model.generate_content.side_effect = Exception("Persistent error")

        mock_genai.GenerativeModel.return_value = mock_model

        client = GeminiClient(api_key="test_key", max_retries=2)
        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(Exception, match="Persistent error"):
            client.send_message(messages)

        assert mock_model.generate_content.call_count == 2

    @patch('src.services.gemini_client.genai')
    def test_simple_query(self, mock_genai):
        """Test simple query method."""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Simple answer"
        mock_model.generate_content.return_value = mock_response

        mock_genai.GenerativeModel.return_value = mock_model

        client = GeminiClient(api_key="test_key")
        response = client.simple_query("What is AI?")

        assert response == "Simple answer"

    @patch('src.services.gemini_client.genai')
    def test_simple_query_with_system(self, mock_genai):
        """Test simple query with system prompt."""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Expert answer"
        mock_model.generate_content.return_value = mock_response

        mock_genai.GenerativeModel.return_value = mock_model

        client = GeminiClient(api_key="test_key")
        response = client.simple_query(
            "Explain quantum computing",
            system="You are a physics professor.",
            temperature=0.3
        )

        assert response == "Expert answer"

    @patch('src.services.gemini_client.genai')
    def test_analyze_with_context(self, mock_genai):
        """Test context-based analysis."""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Contextual analysis"
        mock_model.generate_content.return_value = mock_response

        mock_genai.GenerativeModel.return_value = mock_model

        client = GeminiClient(api_key="test_key")
        response = client.analyze_with_context(
            context="The document describes climate change impacts.",
            query="What are the main threats?",
            system="You are an environmental scientist."
        )

        assert response == "Contextual analysis"
        # Verify context and query were included
        call_args = mock_model.generate_content.call_args
        prompt = call_args[0][0]
        assert "climate change" in prompt.lower()
        assert "main threats" in prompt.lower()

    @patch('src.services.gemini_client.genai')
    def test_structured_decision_success(self, mock_genai):
        """Test structured decision making."""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = """CHOICE: 2
SCORE: 85
REASONING: Option 2 provides the best balance of features and performance."""
        mock_model.generate_content.return_value = mock_response

        mock_genai.GenerativeModel.return_value = mock_model

        client = GeminiClient(api_key="test_key")
        options = [
            {"name": "Option A", "cost": 100},
            {"name": "Option B", "cost": 200},
            {"name": "Option C", "cost": 150}
        ]

        result = client.structured_decision(
            options=options,
            criteria="Choose the best value for money",
            context="Budget is limited"
        )

        assert result['choice'] == 1  # 0-indexed, so option 2 becomes index 1
        assert result['score'] == 85
        assert "balance" in result['reasoning'].lower()

    @patch('src.services.gemini_client.genai')
    def test_structured_decision_invalid_choice(self, mock_genai):
        """Test structured decision with out-of-bounds choice."""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = """CHOICE: 10
SCORE: 50
REASONING: Invalid choice number"""
        mock_model.generate_content.return_value = mock_response

        mock_genai.GenerativeModel.return_value = mock_model

        client = GeminiClient(api_key="test_key")
        options = [
            {"name": "Option A"},
            {"name": "Option B"}
        ]

        result = client.structured_decision(
            options=options,
            criteria="Choose one"
        )

        # Should clamp to valid range
        assert 0 <= result['choice'] < len(options)

    @patch('src.services.gemini_client.genai')
    def test_structured_decision_with_error(self, mock_genai):
        """Test structured decision error handling."""
        mock_model = Mock()
        mock_model.generate_content.side_effect = Exception("API Error")

        mock_genai.GenerativeModel.return_value = mock_model

        client = GeminiClient(api_key="test_key")
        options = [{"name": "A"}, {"name": "B"}]

        result = client.structured_decision(
            options=options,
            criteria="Choose one"
        )

        # Should return fallback
        assert result['choice'] == 0
        assert result['score'] == 0
        assert "Error" in result['reasoning']

    @patch('src.services.gemini_client.genai')
    def test_parse_decision_response_complete(self, mock_genai):
        """Test parsing complete decision response."""
        mock_genai.GenerativeModel.return_value = Mock()

        client = GeminiClient(api_key="test_key")
        response = """CHOICE: 3
SCORE: 92
REASONING: This option provides superior quality and performance metrics."""

        result = client._parse_decision_response(response, num_options=5)

        assert result['choice'] == 2  # 0-indexed
        assert result['score'] == 92
        assert "superior quality" in result['reasoning']

    @patch('src.services.gemini_client.genai')
    def test_parse_decision_response_partial(self, mock_genai):
        """Test parsing partial decision response."""
        mock_genai.GenerativeModel.return_value = Mock()

        client = GeminiClient(api_key="test_key")
        response = """CHOICE: 1
Some reasoning without the REASONING prefix."""

        result = client._parse_decision_response(response, num_options=3)

        assert result['choice'] == 0  # 0-indexed
        assert result['score'] == 50  # Default
        assert isinstance(result['reasoning'], str)

    @patch('src.services.gemini_client.genai')
    def test_parse_decision_response_malformed(self, mock_genai):
        """Test parsing malformed decision response."""
        mock_genai.GenerativeModel.return_value = Mock()

        client = GeminiClient(api_key="test_key")
        response = "Invalid response format"

        result = client._parse_decision_response(response, num_options=2)

        assert result['choice'] == 0
        assert result['score'] == 50
        assert result['reasoning'] == response

    @patch('src.services.gemini_client.genai')
    def test_format_dict(self, mock_genai):
        """Test dictionary formatting."""
        mock_genai.GenerativeModel.return_value = Mock()

        client = GeminiClient(api_key="test_key")
        data = {
            "name": "Test",
            "value": 123,
            "nested": {"key": "value"},
            "list": [1, 2, 3]
        }

        formatted = client._format_dict(data)

        assert "name: Test" in formatted
        assert "value: 123" in formatted
        assert isinstance(formatted, str)
        assert len(formatted.split('\n')) >= 4

    @patch('src.services.gemini_client.genai')
    def test_exponential_backoff(self, mock_genai):
        """Test exponential backoff on retries."""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Success"

        # Fail twice with rate limit, then succeed
        mock_model.generate_content.side_effect = [
            Exception("429 rate limit"),
            Exception("429 rate limit"),
            mock_response
        ]

        mock_genai.GenerativeModel.return_value = mock_model

        with patch('src.services.gemini_client.time.sleep') as mock_sleep:
            client = GeminiClient(api_key="test_key", retry_delay=1.0)
            messages = [{"role": "user", "content": "Test"}]

            response = client.send_message(messages)

            assert response == "Success"
            # Verify exponential backoff: 1.0, 2.0
            sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
            assert sleep_calls[0] == 1.0  # First retry
            assert sleep_calls[1] == 2.0  # Second retry (2^1)

    @patch('src.services.gemini_client.genai')
    def test_message_conversion_user_only(self, mock_genai):
        """Test message format conversion for user messages."""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Response"
        mock_model.generate_content.return_value = mock_response

        mock_genai.GenerativeModel.return_value = mock_model

        client = GeminiClient(api_key="test_key")
        messages = [{"role": "user", "content": "Hello"}]

        client.send_message(messages)

        call_args = mock_model.generate_content.call_args
        prompt = call_args[0][0]
        assert prompt == "Hello"

    @patch('src.services.gemini_client.genai')
    def test_max_tokens_override(self, mock_genai):
        """Test max_tokens parameter override."""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Response"
        mock_model.generate_content.return_value = mock_response

        mock_genai.GenerativeModel.return_value = mock_model

        client = GeminiClient(api_key="test_key", max_tokens=1024)
        messages = [{"role": "user", "content": "Test"}]

        client.send_message(messages, max_tokens=2048)

        call_args = mock_model.generate_content.call_args
        gen_config = call_args[1]['generation_config']
        assert gen_config['max_output_tokens'] == 2048
