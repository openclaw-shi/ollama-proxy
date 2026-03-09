"""Copilot SDKクライアントモジュール

Copilot SDKを使ってOllama互換APIを提供する
"""

import asyncio
from typing import Any

from copilot import CopilotClient, SessionEventType


class CopilotClientManager:
    """Copilot SDKクライアントマネージャー

    リクエストごとに新しいセッションを作成してOllama互換APIを提供する
    """

    def __init__(self) -> None:
        self._client: CopilotClient | None = None

    async def start(self) -> None:
        """クライアントを開始"""
        if self._client is None:
            self._client = CopilotClient()
            await self._client.start()

    async def stop(self) -> None:
        """クライアントを停止"""
        if self._client is not None:
            await self._client.stop()
            self._client = None

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
        if self._client is None:
            await self.start()

        session = await self._client.create_session(
            {"model": model, "streaming": False}
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
            await asyncio.wait_for(
                asyncio.Event().wait(),
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
