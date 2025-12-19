"""
Unit tests for the LLM Client module.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import httpx

from backend.services.llm_client import (
    OllamaClient,
    LLMConfig,
    LLMResponse,
    LLMError,
    OllamaConnectionError,
    OllamaTimeoutError,
    OllamaModelError,
)


class TestLLMConfig:
    """Tests for LLMConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = LLMConfig()
        
        assert config.base_url == "http://localhost:11434"
        assert config.model == "llama3.2"
        assert config.timeout_seconds == 30.0
        assert config.max_retries == 2
        assert config.temperature == 0.7
        assert config.enable_fallback is True
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = LLMConfig(
            base_url="http://custom:8080",
            model="custom-model",
            timeout_seconds=60.0,
            temperature=0.5
        )
        
        assert config.base_url == "http://custom:8080"
        assert config.model == "custom-model"
        assert config.timeout_seconds == 60.0
        assert config.temperature == 0.5


class TestOllamaClient:
    """Tests for OllamaClient class."""
    
    def test_init_default_config(self):
        """Test initialization with default config."""
        client = OllamaClient()
        
        assert client.config.base_url == "http://localhost:11434"
        assert client.config.model == "llama3.2"
    
    def test_init_custom_config(self):
        """Test initialization with custom config."""
        config = LLMConfig(model="custom-model")
        client = OllamaClient(config=config)
        
        assert client.config.model == "custom-model"
    
    def test_build_payload_basic(self):
        """Test payload building with basic parameters."""
        client = OllamaClient()
        
        payload = client._build_payload("Hello", system="You are helpful")
        
        assert payload["model"] == "llama3.2"
        assert payload["prompt"] == "Hello"
        assert payload["system"] == "You are helpful"
        assert payload["stream"] is False
        assert "options" in payload
    
    def test_build_payload_with_options(self):
        """Test payload building with custom options."""
        client = OllamaClient()
        
        payload = client._build_payload(
            "Hello",
            temperature=0.5,
            num_predict=100
        )
        
        assert payload["options"]["temperature"] == 0.5
        assert payload["options"]["num_predict"] == 100
    
    def test_fallback_response(self):
        """Test fallback response generation."""
        config = LLMConfig(fallback_response="Fallback text")
        client = OllamaClient(config=config)
        
        import time
        start = time.time()
        response = client._fallback_response(start)
        
        assert response.text == "Fallback text"
        assert response.model == "fallback"
        assert response.error is not None
        assert response.done is True


class TestOllamaClientWithMocks:
    """Tests for OllamaClient with mocked HTTP responses."""
    
    @patch.object(httpx.Client, 'get')
    def test_is_available_success(self, mock_get):
        """Test is_available returns True when Ollama is running."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        client = OllamaClient()
        client._sync_client = httpx.Client()
        
        assert client.is_available() is True
    
    @patch.object(httpx.Client, 'get')
    def test_is_available_connection_error(self, mock_get):
        """Test is_available returns False on connection error."""
        mock_get.side_effect = httpx.ConnectError("Connection refused")
        
        client = OllamaClient()
        client._sync_client = httpx.Client()
        
        assert client.is_available() is False
    
    @patch.object(httpx.Client, 'post')
    def test_generate_success(self, mock_post):
        """Test successful generation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Generated text",
            "model": "llama3.2",
            "done": True,
            "prompt_eval_count": 10,
            "eval_count": 20
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        client = OllamaClient()
        client._sync_client = httpx.Client()
        
        response = client.generate("Hello")
        
        assert response.text == "Generated text"
        assert response.model == "llama3.2"
        assert response.done is True
    
    @patch.object(httpx.Client, 'post')
    def test_generate_connection_error_with_fallback(self, mock_post):
        """Test generation falls back on connection error."""
        mock_post.side_effect = httpx.ConnectError("Connection refused")
        
        config = LLMConfig(
            enable_fallback=True,
            fallback_response="Fallback",
            max_retries=0
        )
        client = OllamaClient(config=config)
        client._sync_client = httpx.Client()
        
        response = client.generate("Hello")
        
        assert response.text == "Fallback"
        assert response.model == "fallback"
    
    @patch.object(httpx.Client, 'post')
    def test_generate_connection_error_without_fallback(self, mock_post):
        """Test generation raises error when fallback disabled."""
        mock_post.side_effect = httpx.ConnectError("Connection refused")
        
        config = LLMConfig(enable_fallback=False, max_retries=0)
        client = OllamaClient(config=config)
        client._sync_client = httpx.Client()
        
        with pytest.raises(OllamaConnectionError):
            client.generate("Hello")
    
    @patch.object(httpx.Client, 'post')
    def test_generate_timeout_with_fallback(self, mock_post):
        """Test generation falls back on timeout."""
        mock_post.side_effect = httpx.TimeoutException("Timeout")
        
        config = LLMConfig(
            enable_fallback=True,
            fallback_response="Timeout fallback",
            max_retries=0
        )
        client = OllamaClient(config=config)
        client._sync_client = httpx.Client()
        
        response = client.generate("Hello")
        
        assert response.text == "Timeout fallback"
    
    @patch.object(httpx.Client, 'post')
    def test_generate_model_not_found(self, mock_post):
        """Test generation raises error when model not found."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found",
            request=Mock(),
            response=mock_response
        )
        mock_post.return_value = mock_response
        
        config = LLMConfig(enable_fallback=False, max_retries=0)
        client = OllamaClient(config=config)
        client._sync_client = httpx.Client()
        
        with pytest.raises(OllamaModelError):
            client.generate("Hello")


class TestLLMResponse:
    """Tests for LLMResponse dataclass."""
    
    def test_response_creation(self):
        """Test LLMResponse creation."""
        response = LLMResponse(
            text="Hello",
            model="llama3.2",
            total_duration_ms=100.0
        )
        
        assert response.text == "Hello"
        assert response.model == "llama3.2"
        assert response.total_duration_ms == 100.0
        assert response.done is True
        assert response.error is None
    
    def test_response_with_error(self):
        """Test LLMResponse with error."""
        response = LLMResponse(
            text="Fallback",
            model="fallback",
            total_duration_ms=50.0,
            error="Connection failed"
        )
        
        assert response.error == "Connection failed"
