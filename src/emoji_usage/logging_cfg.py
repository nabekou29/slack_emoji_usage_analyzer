"""ロギング設定モジュール"""

import logging
import sys
from rich.logging import RichHandler
from rich.console import Console

from .config import Settings

# グローバル設定の読み込み
settings = Settings()

# Rich コンソールの設定
console = Console()

# ロガーの設定
logger = logging.getLogger("emoji_usage")
logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

# Rich ハンドラーの追加（まだ追加されていない場合のみ）
if not logger.handlers:
    rich_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=False,
        rich_tracebacks=True,
    )
    rich_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(rich_handler)

# 他のロガーのレベルを調整
logging.getLogger("slack_sdk").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
