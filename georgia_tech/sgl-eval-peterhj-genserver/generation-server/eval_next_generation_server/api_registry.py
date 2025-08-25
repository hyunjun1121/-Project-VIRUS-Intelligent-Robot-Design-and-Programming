from typing import Any, Optional
from dataclasses import dataclass, field
import os

# FIXME: pydantic.
@dataclass
class OpenaiModel:
    id: str = None
    created: int = None
    object: str = "model"
    owned_by: str = None

@dataclass
class APIEndpoint:
    name: str = None
    api_url: str = None
    api_key: str = None
    protocol: str = None
    domain: str = None

@dataclass
class APIModel:
    model_path: str = None
    default_sampling_params: dict = None
    endpoint_model_path: str = None
    endpoint_extra_params: dict = None
    endpoint: APIEndpoint = None

    def to_openai(self) -> OpenaiModel:
        return OpenaiModel(
            id=self.model_path,
            created=0,
            owned_by=self.endpoint.domain,
        )

@dataclass
class APIRegistry:
    environ: dict[str, str] = field(default_factory=dict)
    endpoints: dict[str, Any] = field(default_factory=dict)
    endpoint_aliases: dict[str, str] = field(default_factory=dict)
    models: dict[str, Any] = field(default_factory=dict)
    model_aliases: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        self._register_all()

    def get_env(self, key: str) -> Optional[str]:
        v = self.environ.get(key, None)
        if v is None:
            v = os.environ.get(key, None)
            if v is None:
                print(f"DEBUG: APIRegistry: warning: missing env var {repr(key)}")
            else:
                self.environ[key] = v
        return v

    def find_endpoint(self, name: str) -> Optional[APIEndpoint]:
        if name in self.endpoint_aliases:
            name = self.endpoint_aliases[name]
        return self.endpoints.get(name, None)

    def find_model(self, model_path: str) -> Optional[APIModel]:
        model_key = model_path.lower()
        if model_key in self.model_aliases:
            model_key = self.model_aliases[model_key]
        return self.models.get(model_key, None)

    def register_endpoint(self, name: str, aliases: list[str] = [], **kwargs):
        if name in self.endpoints:
            raise KeyError
        for alias_name in aliases:
            if alias_name in self.endpoint_aliases:
                raise KeyError
            self.endpoint_aliases[alias_name] = name
        self.endpoints[name] = APIEndpoint(name=name, **kwargs)

    def register_model(self, endpoint_name: str, model_path: str, aliases: list[str] = [], **kwargs):
        model_key = model_path.lower()
        if model_key in self.models:
            raise KeyError
        for alias_path in aliases:
            alias_key = alias_path.lower()
            if alias_key in self.model_aliases:
                raise KeyError
            self.endpoint_aliases[alias_key] = model_key
        endpoint = self.find_endpoint(endpoint_name)
        self.models[model_key] = APIModel(
            endpoint=endpoint,
            model_path=model_path,
            **kwargs
        )

    def _register_all(self):
        self._register_all_endpoints()
        if self.find_endpoint("anthropic"):
            self._register_anthropic_models()
        if self.find_endpoint("deepseek"):
            self._register_deepseek_models()
        if self.find_endpoint("gemini"):
            self._register_gemini_models()
        if self.find_endpoint("openai"):
            self._register_openai_models()
        if self.find_endpoint("together"):
            self._register_together_models()
        if self.find_endpoint("xai"):
            self._register_xai_models()

    def _register_all_endpoints(self):
        api_key = self.get_env("ANTHROPIC_API_KEY")
        if api_key is not None:
            self.register_endpoint(
                "anthropic", ["anthropic.com"],
                api_url="https://api.anthropic.com",
                api_key=api_key.rstrip(),
                protocol="anthropic",
                domain="anthropic.com",
            )
        api_key = self.get_env("DEEPSEEK_API_KEY")
        if api_key is not None:
            self.register_endpoint(
                "deepseek", ["deepseek-ai", "deepseek.com"],
                api_url="https://api.deepseek.com",
                api_key=api_key.rstrip(),
                protocol="deepseek",
                domain="deepseek.com",
            )
        api_key = self.get_env("GEMINI_API_KEY")
        if api_key is not None:
            self.register_endpoint(
                "gemini",
                api_url="https://generativelanguage.googleapis.com",
                api_key=api_key.rstrip(),
                protocol="gemini",
                domain="google.com",
            )
        api_key = self.get_env("OPENAI_API_KEY")
        if api_key is not None:
            self.register_endpoint(
                "openai", ["openai.com"],
                api_url="https://api.openai.com",
                api_key=api_key.rstrip(),
                protocol="openai",
                domain="openai.com",
            )
        api_key = self.get_env("TOGETHER_API_KEY")
        if api_key is not None:
            self.register_endpoint(
                "together", ["together.ai", "together.xyz"],
                api_url="https://api.together.xyz",
                api_key=api_key.rstrip(),
                protocol="openai",
                domain="together.xyz",
            )
        api_key = self.get_env("XAI_API_KEY")
        if api_key is not None:
            self.register_endpoint(
                "xai", ["x.ai"],
                api_url="https://api.x.ai",
                api_key=api_key.rstrip(),
                protocol="openai",
                domain="x.ai",
            )

    def _register_anthropic_models(self):
        self.register_model(
            "anthropic",
            "anthropic/claude-4-sonnet-thinking-off",
            endpoint_model_path="claude-sonnet-4-20250514",
            endpoint_extra_params={
                "thinking": {
                    "type": "disabled",
                },
            },
        )
        self.register_model(
            "anthropic",
            "anthropic/claude-4-sonnet-thinking-on-10k",
            endpoint_model_path="claude-sonnet-4-20250514",
            endpoint_extra_params={
                "thinking": {
                    "type": "enabled",
                    "budget_tokens": 10000,
                },
            },
        )
        self.register_model(
            "anthropic",
            "anthropic/claude-4-opus-thinking-off",
            endpoint_model_path="claude-opus-4-20250514",
            endpoint_extra_params={
                "thinking": {
                    "type": "disabled",
                },
            },
        )
        self.register_model(
            "anthropic",
            "anthropic/claude-4-opus-thinking-on-10k",
            endpoint_model_path="claude-opus-4-20250514",
            endpoint_extra_params={
                "thinking": {
                    "type": "enabled",
                    "budget_tokens": 10000,
                },
            },
        )

    def _register_deepseek_models(self):
        self.register_model(
            "deepseek",
            "deepseek-ai/DeepSeek-V3-0324",
            endpoint_model_path="deepseek-chat",
        )
        self.register_model(
            "deepseek",
            "deepseek-ai/DeepSeek-R1-0528",
            endpoint_model_path="deepseek-reasoner",
        )

    def _register_gemini_models(self):
        self.register_model(
            "gemini",
            "google/gemini-2.5-flash-thinking-off",
            endpoint_model_path="models/gemini-2.5-flash",
            endpoint_extra_params={
                "generationConfig": {
                    "thinkingConfig": {
                        "thinkingBudget": 0,
                    }
                },
            },
        )
        self.register_model(
            "gemini",
            "google/gemini-2.5-flash-thinking-on",
            endpoint_model_path="models/gemini-2.5-flash",
            # TODO(peter): extra params dict must be _merged_.
            endpoint_extra_params={
                "generationConfig": {
                    "thinkingConfig": {
                        "includeThoughts": True,
                        "thinkingBudget": -1,
                    }
                },
            },
        )
        self.register_model(
            "gemini",
            "google/gemini-2.5-pro-thinking-off",
            endpoint_model_path="models/gemini-2.5-pro",
            endpoint_extra_params={
                "generationConfig": {
                    "thinkingConfig": {
                        "thinkingBudget": 0,
                    }
                },
            },
        )
        self.register_model(
            "gemini",
            "google/gemini-2.5-pro-thinking-on",
            endpoint_model_path="models/gemini-2.5-pro",
            endpoint_extra_params={
                "generationConfig": {
                    "thinkingConfig": {
                        "includeThoughts": True,
                        "thinkingBudget": -1,
                    }
                },
            },
        )

    def _register_openai_models(self):
        self.register_model(
            "openai",
            "openai/gpt-4o-mini",
            ["gpt-4o-mini"],
            endpoint_model_path="gpt-4o-mini-2024-07-18",
        )
        self.register_model(
            "openai",
            "openai/gpt-4o-20240806",
            ["gpt-4o-20240806"],
            endpoint_model_path="gpt-4o-2024-08-06",
        )
        self.register_model(
            "openai",
            "openai/gpt-4.1-nano",
            ["gpt-4.1-nano"],
            endpoint_model_path="gpt-4.1-nano-2025-04-14",
        )
        self.register_model(
            "openai",
            "openai/gpt-4.1-mini",
            ["gpt-4.1-mini"],
            endpoint_model_path="gpt-4.1-mini-2025-04-14",
        )
        self.register_model(
            "openai",
            "openai/gpt-4.1",
            ["gpt-4.1"],
            endpoint_model_path="gpt-4.1-2025-04-14",
        )
        self.register_model(
            "openai",
            "openai/o3-high",
            ["o3-high"],
            endpoint_model_path="o3-2025-04-16",
            endpoint_extra_params={
                "reasoning_effort": "high",
            },
        )
        self.register_model(
            "openai",
            "openai/o4-mini-high",
            ["o4-mini-high"],
            endpoint_model_path="o4-mini-2025-04-16",
            endpoint_extra_params={
                "reasoning_effort": "high",
            },
        )
        self.register_model(
            "openai",
            "openai/gpt-5",
            ["gpt-5"],
            endpoint_model_path="gpt-5-2025-08-07",
        )

    def _register_together_models(self):
        self.register_model(
            "together",
            "togetherai/Qwen/Qwen3-235B-A22B-FP8",
            ["together/Qwen/Qwen3-235B-A22B-FP8"],
            endpoint_model_path="Qwen/Qwen3-235B-A22B-fp8-tput",
        )
        self.register_model(
            "together",
            "togetherai/Qwen/Qwen3-235B-A22B-Instruct-2507-FP8",
            ["together/Qwen/Qwen3-235B-A22B-Instruct-2507-FP8"],
            endpoint_model_path="Qwen/Qwen3-235B-A22B-Instruct-2507-tput",
        )
        self.register_model(
            "together",
            "togetherai/Qwen/Qwen3-235B-A22B-Thinking-2507-FP8",
            ["together/Qwen/Qwen3-235B-A22B-Thinking-2507-FP8"],
            endpoint_model_path="Qwen/Qwen3-235B-A22B-Thinking-2507",
        )
        self.register_model(
            "together",
            "togetherai/Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8",
            ["together/Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8"],
            endpoint_model_path="Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8",
        )
        self.register_model(
            "together",
            "togetherai/moonshotai/Kimi-K2-Instruct",
            ["together/moonshotai/Kimi-K2-Instruct"],
            endpoint_model_path="moonshotai/Kimi-K2-Instruct",
        )

    def _register_xai_models(self):
        self.register_model(
            "xai",
            "xai/grok-4",
            ["grok-4"],
            endpoint_model_path="grok-4-0709",
        )
