"""Copilot SDKクライアントモジュール

Copilot SDKを使ってOllama互換APIを提供する
"""

import asyncio
from typing import Any

CopilotClient: Any = None
SessionEventType: Any = None
_copilot_client: Any = None


class CopilotClientManager:
    """Copilot SDKクライアントマネージャー

    リクエストごとに新しいセッションを作成してOllama互換APIを提供する
    """

    def __init__(self) -> None:
        global CopilotClient, SessionEventType, _copilot_client

        try:
            import copilot as _copilot_module

            if hasattr(_copilot_module, "CopilotClient"):
                CopilotClient = _copilot_module.CopilotClient
                if hasattr(_copilot_module, "SessionEventType"):
                    SessionEventType = _copilot_module.SessionEventType
                _copilot_client = CopilotClient()
        except ImportError:
            pass

    def _ensure_copilot(self):
        global _copilot_client, CopilotClient
        if _copilot_client is not None:
            return True
        if CopilotClient is None:
            return False

        try:
            _copilot_client = CopilotClient()
            return True
        except Exception:
            return False

    async def start(self) -> None:
        """クライアントを開始"""
        global _copilot_client
        if _copilot_client is None:
            if not self._ensure_copilot():
                raise RuntimeError(
                    "copilot package is not installed. Install with: pip install github-copilot-sdk"
                )

    async def stop(self) -> None:
        """クライアントを停止"""
        global _copilot_client
        if _copilot_client is not None:
            await _copilot_client.stop()
            _copilot_client = None

    async def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
    ) -> dict[str, Any]:
        """チャットリクエストを処理

        Args:
            model: モデル名
            messages: メッセージリスト

        Returns:
            Ollama形式のレスポンス
        """
        global _copilot_client, CopilotClient

        if CopilotClient is None:
            raise RuntimeError(
                "copilot package is not installed. Install with: pip install github-copilot-sdk"
            )

        if _copilot_client is None:
            _copilot_client = CopilotClient(
                on_permission_request=lambda req, inv: {"kind": "approved"}
            )
            await _copilot_client.start()

        session = await _copilot_client.create_session(
            {
                "model": model,
                "streaming": False,
                "on_permission_request": lambda req, inv: {"kind": "approved"},
            }
        )

        prompt = self._messages_to_prompt(messages)

        result_content = ""
        error_content = None

        def handle_event(event: dict[str, Any]) -> None:
            nonlocal result_content, error_content
            event_type = event.get("type")

            if event_type == SessionEventType.ASSISTANT_MESSAGE:
                result_content = event.get("data", {}).get("content", "")
            elif event_type == SessionEventType.ERROR:
                error_content = event.get("data", {}).get("error", "Unknown error")

        session.on(handle_event)

        try:
            await session.send({"prompt": prompt})
            import asyncio as _asyncio

            await _asyncio.wait_for(
                _asyncio.Event().wait(),
                timeout=120,
            )
        except TimeoutError:
            error_content = "Request timeout"
        except Exception as e:
            error_content = str(e)
        finally:
            await session.close()

        if error_content:
            raise RuntimeError(f"Copilot error: {error_content}")

        return {
            "content": result_content,
            "model": model,
        }

    def _messages_to_prompt(self, messages: list[dict[str, str]]) -> str:
        """メッセージリストをプロンプトに変換

        Args:
            messages: Ollama形式のメッセージ

        Returns:
            Copilot用プロンプト
        """
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")

        return "\n".join(prompt_parts)
