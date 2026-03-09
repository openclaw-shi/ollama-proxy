# Ollama Proxy

LiteLLMを使用して、様々なAIプロバイダーのエンドポイントをOllama互換APIとして提供するプロキシサーバーです。

## 概要

Ollama Proxyは、ローカルで動作するOllama風のAPIサーバーを構築し、OpenAI、Anthropic、Google、Azureなど多様なLLMプロバイダーにOllamaクライアントからアクセスできるようにします。

### 主な機能

- **Ollama互換API**: お気に入りのOllamaクライアント（Open WebUI、LLM clientsなど）をそのまま使用可能
- **マルチプロバイダー対応**: LiteLLMがサポートするすべてのLLMプロバイダーに接続可能
- **設定のホットリロード**: `providers.json`を変更すると、サーバーを再起動せずにモデル設定を更新
- **GUIダッシュボード**: StreamlitベースのGUIでモデル管理とテストが可能
- **ストリーミング対応**: 生成・チャット両方のストリーミング出力に対応
- **推論思考（Thinking）対応**: 推論 EffortやThinking Budgetの設定をサポート

## 動作環境

- Python 3.12以上
- [uv](https://docs.astral.sh/uv/)（パッケージマネージャー）

## インストール

```powershell
# プロジェクトの同期と仮想環境の作成
uv sync

# 依存関係の有効化
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
```

## 設定ファイル

### 設定ディレクトリ

デフォルトでは `~/.ollama-proxy/` ディレクトリに設定ファイルを配置します。

### config.json（サーバー設定）

`~/.ollama-proxy/config.json` にサーバー設定を保存します：

```json
{
  "host": "127.0.0.1",
  "port": 11434,
  "providers_file": "~/.ollama-proxy/providers.json",
  "log_level": "info"
}
```

| 設定項目 | 説明 | デフォルト値 |
|---------|------|-------------|
| host | サーバーがバインドするアドレス | 127.0.0.1 |
| port | サーバーが Listenするポート | 11434 |
| providers_file | プロバイダー設定ファイルのパス | ~/.ollama-proxy/providers.json |
| log_level | ログレベル（debug, info, warning, error） | info |

### providers.json（モデル設定）

`~/.ollama-proxy/providers.json` にモデルとプロバイダーのマッピングを定義します：

```json
{
  "openai": {
    "provider": "openai",
    "api_key": "your-api-key-here",
    "models": [
      {
        "name": "gpt-4o",
        "model_name": "gpt-4o"
      }
    ]
  },
  "anthropic": {
    "provider": "anthropic",
    "api_key": "your-api-key-here",
    "models": [
      {
        "name": "claude-sonnet-4-20250514",
        "model_name": "claude-sonnet-4-20250514"
      }
    ]
  },
  "gemini": {
    "provider": "gemini",
    "api_key": "your-api-key-here",
    "models": [
      {
        "name": "gemini-2.0-flash",
        "model_name": "gemini-2.0-flash",
        "reasoning_effort": "high"
      }
    ]
  },
  "custom": {
    "provider": "custom_openai",
    "api_key": "your-api-key",
    "base_url": "https://api.example.com/v1",
    "models": [
      {
        "name": "custom-model",
        "model_name": "custom-model-name",
        "thinking_budget": 4096
      }
    ]
  }
}
```

#### 設定項目説明

| 項目 | 説明 |
|------|------|
| プロバイダーID（トップレベルキー） | Ollamaでのモデル名 접두사（例: `openai:gpt-4o` の場合は `openai`） |
| provider | LiteLLMのプロバイダー名（openai, anthropic, gemini, azure, custom_openaiなど） |
| api_key | APIキー（環境変数からも取得可能） |
| base_url | カスタムエンドポイントのURL（providerがcustom_openaiまたはオープンソースモデル用） |
| models | モデル定義の配列 |
| name | Ollamaでのモデル名（API呼び出し時に使用） |
| model_name | プロバイダーの実際のモデル名 |
| reasoning_effort | 推論 Effort（low, medium, high）- Gemini等対応プロバイダーのみ |
| thinking_budget | Thinking Budget（トークン数）- 対応モデルのみ |
| additional_params | LiteLLMに追加で渡すパラメータ |

#### モデルの呼び出し例

```
ollama list で表示される名前: gpt-4o, claude-sonnet-4-20250514, gemini-2.0-flash, custom-model
```

## 使用方法

### サーバーの起動

```powershell
# 標準起動（ポート11434でlisten）
ollama-proxy-server

# 開発モード（デバッグログ有効）
ollama-proxy-dev

# ポート指定
ollama-proxy-server --port 8080
```

### GUIダッシュボードの起動

```powershell
# Streamlit GUIを起動
uv run streamlit run py_pro/src/ollama_proxy/gui/app.py
```

ブラウザで `http://localhost:8501` にアクセスするとダッシュボードが表示されます。

## APIエンドポイント

Ollama Proxyは以下のOllama APIエンドポイントを提供します：

| エンドポイント | メソッド | 説明 |
|---------------|---------|------|
| / | GET | ヘルスチェック |
| /api/version | POST | バージョン情報取得 |
| /api/tags | GET | 利用可能なモデル一覧 |
| /api/show | POST | モデル情報取得 |
| /api/generate | POST | テキスト生成（非ストリーミング/ストリーミング） |
| /api/chat | POST | チャット生成（非ストリーミング/ストリーミング） |
| /api/embed | POST | エンベディング生成（未実装） |
| /api/ps | GET | 実行中のモデル一覧 |

### 使用例

#### チャットAPIの使用

```powershell
curl http://127.0.0.1:11434/api/chat -d '{
  "model": "gpt-4o",
  "messages": [
    {"role": "user", "content": "こんにちは！"}
  ],
  "stream": false
}'
```

#### ストリーミング生成

```powershell
curl http://127.0.0.1:11434/api/generate -d '{
  "model": "gpt-4o",
  "prompt": "こんにちは",
  "stream": true
}'
```

## プロジェクト構造

```
ollama-proxy/
├── py_pro/
│   └── src/
│       └── ollama_proxy/
│           ├── __init__.py      # パッケージ初期化
│           ├── api.py           # FastAPIサーバー実装
│           ├── config.py        # 設定管理（ファイル監視含む）
│           ├── converter.py     # Ollama形式への変換
│           ├── tracker.py       # 使用量トラッキング
│           ├── storage.py       # データ保存
│           └── gui/
│               ├── app.py       # Streamlit GUI
│               ├── dashboard.py # ダッシュボードUI
│               └── settings.py  # 設定画面
├── chat_test/
│   └── テスト用チャットクライアント
└── README.md
```

## 開発

### テストの実行

```powershell
uv run pytest
```

### リントとフォーマット

```powershell
# リントチェック
uv run ruff check

# 自動修正
uv run ruff check --fix

# フォーマット
uv run ruff format
```

### 型チェック

```powershell
uv run mypy .
```

## ライセンス

MIT License
