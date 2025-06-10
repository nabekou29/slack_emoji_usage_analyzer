"""設定管理モジュール"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """アプリケーション設定"""

    # 必須設定（実行時にチェック）
    slack_token: str = Field(default="", description="Slack APIトークン")

    # レート制御設定
    min_interval_sec: float = Field(
        default=5.0, description="通常API呼び出し間隔（秒）"
    )
    max_retry: int = Field(default=3, description="429エラー時の最大リトライ回数")

    # 集計設定
    months: int = Field(default=12, description="集計対象期間（月数）")
    output_path: str = Field(default="emoji_usage.csv", description="出力ファイルパス")

    # ログ設定
    log_level: str = Field(default="INFO", description="ログレベル")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "env_prefix": "",
        "case_sensitive": False,
    }
