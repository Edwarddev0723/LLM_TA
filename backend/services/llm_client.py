"""
LLM Client for the AI Math Tutor system.
Provides integration with Ollama for local LLM inference.
"""
import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, AsyncGenerator, Generator
from enum import Enum
import logging

import httpx

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass


class OllamaConnectionError(LLMError):
    """Raised when unable to connect to Ollama service."""
    pass


class OllamaTimeoutError(LLMError):
    """Raised when LLM generation times out."""
    pass


class OllamaModelError(LLMError):
    """Raised when there's an issue with the model."""
    pass


@dataclass
class LLMResponse:
    """Response from the LLM."""
    text: str
    model: str
    total_duration_ms: float
    prompt_eval_count: int = 0
    eval_count: int = 0
    done: bool = True
    error: Optional[str] = None


@dataclass
class LLMConfig:
    """Configuration for the LLM client."""
    base_url: str = "http://localhost:11434"
    model: str = "llama3.2"
    timeout_seconds: float = 30.0
    max_retries: int = 2
    temperature: float = 0.7
    top_p: float = 0.9
    num_ctx: int = 4096
    
    # Fallback configuration
    fallback_response: str = "抱歉，我目前無法處理這個請求。請稍後再試。"
    enable_fallback: bool = True


class OllamaClient:
    """
    Client for interacting with Ollama API.
    
    Provides:
    - Synchronous and asynchronous generation
    - Timeout handling with configurable limits
    - Error recovery with fallback responses
    - Connection health checking
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Initialize the Ollama client.
        
        Args:
            config: Optional LLMConfig. Uses defaults if not provided.
        """
        self.config = config or LLMConfig()
        self._sync_client: Optional[httpx.Client] = None
        self._async_client: Optional[httpx.AsyncClient] = None
    
    @property
    def sync_client(self) -> httpx.Client:
        """Get or create synchronous HTTP client."""
        if self._sync_client is None:
            self._sync_client = httpx.Client(
                base_url=self.config.base_url,
                timeout=httpx.Timeout(self.config.timeout_seconds)
            )
        return self._sync_client
    
    @property
    def async_client(self) -> httpx.AsyncClient:
        """Get or create asynchronous HTTP client."""
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=httpx.Timeout(self.config.timeout_seconds)
            )
        return self._async_client

    def is_available(self) -> bool:
        """
        Check if Ollama service is available.
        
        Returns:
            True if Ollama is running and accessible
        """
        try:
            response = self.sync_client.get("/api/tags")
            return response.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False
        except Exception as e:
            logger.warning(f"Unexpected error checking Ollama availability: {e}")
            return False
    
    async def is_available_async(self) -> bool:
        """
        Asynchronously check if Ollama service is available.
        
        Returns:
            True if Ollama is running and accessible
        """
        try:
            response = await self.async_client.get("/api/tags")
            return response.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False
        except Exception as e:
            logger.warning(f"Unexpected error checking Ollama availability: {e}")
            return False
    
    def list_models(self) -> list[str]:
        """
        List available models in Ollama.
        
        Returns:
            List of model names
            
        Raises:
            OllamaConnectionError: If unable to connect to Ollama
        """
        try:
            response = self.sync_client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except httpx.ConnectError as e:
            raise OllamaConnectionError(
                f"無法連接到 Ollama 服務。請確認 Ollama 已啟動。錯誤: {e}"
            )
        except Exception as e:
            raise OllamaConnectionError(f"獲取模型列表失敗: {e}")
    
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The user prompt
            system: Optional system prompt
            **kwargs: Additional parameters to pass to Ollama
            
        Returns:
            LLMResponse with the generated text
            
        Raises:
            OllamaConnectionError: If unable to connect
            OllamaTimeoutError: If generation times out
            OllamaModelError: If there's a model-related error
        """
        start_time = time.time()
        
        # Build request payload
        payload = self._build_payload(prompt, system, **kwargs)
        
        for attempt in range(self.config.max_retries + 1):
            try:
                response = self.sync_client.post(
                    "/api/generate",
                    json=payload
                )
                response.raise_for_status()
                
                data = response.json()
                
                return LLMResponse(
                    text=data.get("response", ""),
                    model=data.get("model", self.config.model),
                    total_duration_ms=(time.time() - start_time) * 1000,
                    prompt_eval_count=data.get("prompt_eval_count", 0),
                    eval_count=data.get("eval_count", 0),
                    done=data.get("done", True)
                )
                
            except httpx.ConnectError as e:
                if attempt == self.config.max_retries:
                    if self.config.enable_fallback:
                        return self._fallback_response(start_time)
                    raise OllamaConnectionError(
                        f"無法連接到 Ollama 服務: {e}"
                    )
                logger.warning(f"Connection attempt {attempt + 1} failed, retrying...")
                
            except httpx.TimeoutException as e:
                if attempt == self.config.max_retries:
                    if self.config.enable_fallback:
                        return self._fallback_response(start_time)
                    raise OllamaTimeoutError(
                        f"LLM 生成超時 (>{self.config.timeout_seconds}秒): {e}"
                    )
                logger.warning(f"Timeout on attempt {attempt + 1}, retrying...")
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise OllamaModelError(
                        f"模型 '{self.config.model}' 未找到。請執行: ollama pull {self.config.model}"
                    )
                if self.config.enable_fallback:
                    return self._fallback_response(start_time)
                raise LLMError(f"HTTP 錯誤: {e}")
        
        # Should not reach here, but just in case
        return self._fallback_response(start_time)

    async def generate_async(
        self,
        prompt: str,
        system: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Asynchronously generate a response from the LLM.
        
        Args:
            prompt: The user prompt
            system: Optional system prompt
            **kwargs: Additional parameters to pass to Ollama
            
        Returns:
            LLMResponse with the generated text
        """
        start_time = time.time()
        
        payload = self._build_payload(prompt, system, **kwargs)
        
        for attempt in range(self.config.max_retries + 1):
            try:
                response = await self.async_client.post(
                    "/api/generate",
                    json=payload
                )
                response.raise_for_status()
                
                data = response.json()
                
                return LLMResponse(
                    text=data.get("response", ""),
                    model=data.get("model", self.config.model),
                    total_duration_ms=(time.time() - start_time) * 1000,
                    prompt_eval_count=data.get("prompt_eval_count", 0),
                    eval_count=data.get("eval_count", 0),
                    done=data.get("done", True)
                )
                
            except httpx.ConnectError as e:
                if attempt == self.config.max_retries:
                    if self.config.enable_fallback:
                        return self._fallback_response(start_time)
                    raise OllamaConnectionError(f"無法連接到 Ollama 服務: {e}")
                logger.warning(f"Connection attempt {attempt + 1} failed, retrying...")
                
            except httpx.TimeoutException as e:
                if attempt == self.config.max_retries:
                    if self.config.enable_fallback:
                        return self._fallback_response(start_time)
                    raise OllamaTimeoutError(
                        f"LLM 生成超時 (>{self.config.timeout_seconds}秒): {e}"
                    )
                logger.warning(f"Timeout on attempt {attempt + 1}, retrying...")
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise OllamaModelError(
                        f"模型 '{self.config.model}' 未找到"
                    )
                if self.config.enable_fallback:
                    return self._fallback_response(start_time)
                raise LLMError(f"HTTP 錯誤: {e}")
        
        return self._fallback_response(start_time)
    
    def generate_stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        **kwargs
    ) -> Generator[str, None, None]:
        """
        Generate a streaming response from the LLM.
        
        Args:
            prompt: The user prompt
            system: Optional system prompt
            **kwargs: Additional parameters
            
        Yields:
            Text chunks as they are generated
        """
        payload = self._build_payload(prompt, system, stream=True, **kwargs)
        
        try:
            with self.sync_client.stream(
                "POST",
                "/api/generate",
                json=payload
            ) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
                            
        except httpx.ConnectError:
            if self.config.enable_fallback:
                yield self.config.fallback_response
            else:
                raise OllamaConnectionError("無法連接到 Ollama 服務")
        except httpx.TimeoutException:
            if self.config.enable_fallback:
                yield self.config.fallback_response
            else:
                raise OllamaTimeoutError("LLM 生成超時")
    
    async def generate_stream_async(
        self,
        prompt: str,
        system: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Asynchronously generate a streaming response from the LLM.
        
        Args:
            prompt: The user prompt
            system: Optional system prompt
            **kwargs: Additional parameters
            
        Yields:
            Text chunks as they are generated
        """
        payload = self._build_payload(prompt, system, stream=True, **kwargs)
        
        try:
            async with self.async_client.stream(
                "POST",
                "/api/generate",
                json=payload
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
                            
        except httpx.ConnectError:
            if self.config.enable_fallback:
                yield self.config.fallback_response
            else:
                raise OllamaConnectionError("無法連接到 Ollama 服務")
        except httpx.TimeoutException:
            if self.config.enable_fallback:
                yield self.config.fallback_response
            else:
                raise OllamaTimeoutError("LLM 生成超時")

    def _build_payload(
        self,
        prompt: str,
        system: Optional[str] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Build the request payload for Ollama API.
        
        Args:
            prompt: The user prompt
            system: Optional system prompt
            stream: Whether to stream the response
            **kwargs: Additional parameters
            
        Returns:
            Dictionary payload for the API request
        """
        payload = {
            "model": kwargs.get("model", self.config.model),
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "top_p": kwargs.get("top_p", self.config.top_p),
                "num_ctx": kwargs.get("num_ctx", self.config.num_ctx),
            }
        }
        
        if system:
            payload["system"] = system
        
        # Add any additional options
        for key in ["num_predict", "stop", "seed"]:
            if key in kwargs:
                payload["options"][key] = kwargs[key]
        
        return payload
    
    def _fallback_response(self, start_time: float) -> LLMResponse:
        """
        Create a fallback response when LLM is unavailable.
        
        Args:
            start_time: When the request started
            
        Returns:
            LLMResponse with fallback text
        """
        return LLMResponse(
            text=self.config.fallback_response,
            model="fallback",
            total_duration_ms=(time.time() - start_time) * 1000,
            done=True,
            error="LLM unavailable, using fallback response"
        )
    
    def close(self) -> None:
        """Close the HTTP clients."""
        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None
    
    async def close_async(self) -> None:
        """Asynchronously close the HTTP clients."""
        if self._async_client:
            await self._async_client.aclose()
            self._async_client = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_async()
