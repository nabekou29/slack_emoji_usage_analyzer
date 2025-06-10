# Slack絵文字利用集計ツール (Rate-Limit Friendly版)

Slackワークスペースの絵文字利用状況を月次で集計するツールです。  
Slack Web APIのレート制限を厳格に守り、安全に長時間実行できるように設計されています。

## 特徴

- **Rate-Limit Friendly**: Slack APIの制限を厳格に守る（12 req/min）
- **429エラー対応**: Retry-Afterヘッダーに従った自動リトライ
- **逐次処理**: 並列処理を避け、安定した動作を実現
- **詳細ログ**: 進捗状況とエラー情報を分かりやすく出力

## インストール

### 1. uvを使用する場合（推奨）

```bash
# uv本体のインストール
curl -Ls https://astral.sh/uv/install.sh | sh

# 仮想環境の作成
uv venv --python 3.12
source .venv/bin/activate

# 依存パッケージのインストール
uv pip install -e .
```

### 2. pipを使用する場合

```bash
# 仮想環境の作成
python -m venv .venv
source .venv/bin/activate

# パッケージのインストール
pip install -e .
```

## 設定

### 1. Slack Appの作成とトークン取得

1. [Slack API](https://api.slack.com/apps)でAppを作成
2. 「OAuth & Permissions」で以下のスコープを設定：

**User Token Scopes（重要）:**

- `search:read` - メッセージ検索用
- `emoji:read` - カスタム絵文字一覧取得用
- `team:read` - ワークスペース情報取得用

3. ワークスペースにインストール
4. **User OAuth Token** (xoxp-で始まる) を取得

### 2. 環境設定

`.env`ファイルを作成し、User Tokenを設定：

```bash
cp .env.example .env
```

`.env`ファイルを編集：

```
SLACK_TOKEN=xoxp-your-user-token-here
```

## 使用方法

```bash
# 基本的な使用方法（12ヶ月分の集計）
emoji-usage

# 集計期間を指定（6ヶ月分）
emoji-usage --months 6

# 出力ファイル名を指定
emoji-usage --output my_emoji_usage.csv

# 標準絵文字のみを対象とする
emoji-usage --only-standard

# カスタム絵文字のみを対象とする
emoji-usage --only-custom

# 標準絵文字を除外する（カスタム絵文字のみ）
emoji-usage --no-standard

# カスタム絵文字を除外する（標準絵文字のみ）
emoji-usage --no-custom

# ヘルプの表示
emoji-usage --help
```

## コマンドラインオプション

| オプション        | 説明                               | 例                    |
| ----------------- | ---------------------------------- | --------------------- |
| `--months`, `-m`  | 集計対象月数                       | `--months 6`          |
| `--output`, `-o`  | 出力ファイルパス                   | `--output report.csv` |
| `--only-standard` | 標準絵文字のみ対象                 | `--only-standard`     |
| `--only-custom`   | カスタム絵文字のみ対象             | `--only-custom`       |
| `--no-standard`   | 標準絵文字を除外                   | `--no-standard`       |
| `--no-custom`     | カスタム絵文字を除外               | `--no-custom`         |
| `--max-emojis`    | 処理する絵文字の最大数（テスト用） | `--max-emojis 10`     |
| `--log-level`     | ログレベル                         | `--log-level DEBUG`   |
| `--verbose`, `-v` | 詳細ログを表示                     | `--verbose`           |

## 環境変数設定

| 設定項目           | デフォルト値      | 説明                           |
| ------------------ | ----------------- | ------------------------------ |
| `SLACK_TOKEN`      | -                 | Slack User APIトークン（必須） |
| `MIN_INTERVAL_SEC` | 5.0               | API呼び出し間隔（秒）          |
| `MAX_RETRY`        | 3                 | 429エラー時の最大リトライ回数  |
| `MONTHS`           | 12                | 集計対象期間（月数）           |
| `OUTPUT_PATH`      | "emoji_usage.csv" | 出力ファイルパス               |
| `LOG_LEVEL`        | "INFO"            | ログレベル                     |

## 出力形式

CSV形式で以下の列が出力されます：

- `emoji`: 絵文字名
- `month`: 対象月（YYYY-MM形式）
- `usage_count`: 使用回数

## 実行時の注意

⚠️ **重要な注意事項**

- 本ツールはSlack Web API Tier-2制限（≈20 req/min）より余裕を持って12 req/minになるようデフォルト設定しています
- SLACK_TOKENを他のツールと共有している場合は`min_interval_sec`をさらに長くしてください
- 処理完了まで数時間～十数時間かかるのは仕様です（絵文字500種類の場合約17時間）

## 開発

### 開発環境のセットアップ

```bash
# 開発用依存関係のインストール
uv pip install -e ".[dev]"

# テストの実行
pytest

# リント
ruff check .

# フォーマット
ruff format .

# リント + フォーマット（一括）
ruff check --fix . && ruff format .

# 型チェック
mypy src/
```

### テスト

```bash
# 全テストの実行
pytest

# カバレッジレポート付き
pytest --cov=emoji_usage --cov-report=html
```

## ライセンス

MIT License