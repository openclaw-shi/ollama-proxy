"""Config tests for Copilot integration"""

import pytest
from unittest.mock import patch

from ollama_proxy.config import ConfigManager, CopilotConfig, LiteLLMConfig


class TestCopilotConfig:
    """CopilotConfigのテスト"""

    def test_copilot_config_creation(self):
        config = CopilotConfig(model_name="gpt-5.4")
        assert config.model_name == "gpt-5.4"
        assert config.additional_params == {}

    def test_copilot_config_with_params(self):
        config = CopilotConfig(
            model_name="claude-sonnet-4.6",
            additional_params={"temperature": 0.7},
        )
        assert config.model_name == "claude-sonnet-4.6"
        assert config.additional_params == {"temperature": 0.7}


class TestConfigManager:
    """ConfigManagerのCopilot関連テスト"""

    @pytest.fixture
    def temp_config_dir(self, tmp_path, monkeypatch):
        config_dir = tmp_path / ".ollama-proxy"
        config_dir.mkdir()
        monkeypatch.setattr(
            "ollama_proxy.config.Path.home",
            lambda: tmp_path,
        )
        return config_dir

    def test_get_copilot_config_returns_none_for_litellm(
        self, temp_config_dir, monkeypatch
    ):
        providers_file = temp_config_dir / "providers.json"
        providers_file.write_text(
            """{
                "openai-model": {
                    "provider": "openai",
                    "models": [{"name": "gpt-4", "model_name": "gpt-4"}]
                }
            }"""
        )

        config = ConfigManager()
        result = config.get_copilot_config("openai-model")
        assert result is None

        config.stop_watching()

    def test_get_copilot_config_returns_config(self, temp_config_dir, monkeypatch):
        providers_file = temp_config_dir / "providers.json"
        providers_file.write_text(
            """{
                "gpt-5.4": {
                    "provider": "copilot",
                    "models": [{"name": "gpt-5.4", "model_name": "gpt-5.4"}]
                }
            }"""
        )

        config = ConfigManager()
        result = config.get_copilot_config("gpt-5.4")
        assert result is not None
        assert result.model_name == "gpt-5.4"

        config.stop_watching()

    def test_get_provider_config_returns_correct_type(self, temp_config_dir):
        providers_file = temp_config_dir / "providers.json"
        providers_file.write_text(
            """{
                "gpt-5.4": {
                    "provider": "copilot",
                    "models": [{"name": "gpt-5.4", "model_name": "gpt-5.4"}]
                },
                "gpt-4": {
                    "provider": "openai",
                    "models": [{"name": "gpt-4", "model_name": "gpt-4"}]
                }
            }"""
        )

        config = ConfigManager()
        copilot_result = config.get_provider_config("gpt-5.4")
        litellm_result = config.get_provider_config("gpt-4")

        assert isinstance(copilot_result, CopilotConfig)
        assert isinstance(litellm_result, LiteLLMConfig)

        config.stop_watching()

    def test_get_litellm_config_returns_none_for_copilot(self, temp_config_dir):
        providers_file = temp_config_dir / "providers.json"
        providers_file.write_text(
            """{
                "gpt-5.4": {
                    "provider": "copilot",
                    "models": [{"name": "gpt-5.4", "model_name": "gpt-5.4"}]
                }
            }"""
        )

        config = ConfigManager()
        result = config.get_litellm_config("gpt-5.4")
        assert result is None

        config.stop_watching()
