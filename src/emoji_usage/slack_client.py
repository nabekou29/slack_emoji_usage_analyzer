"""Slack APIクライアント（レート制限対応）"""

import time
from typing import List, Dict, Any, Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from .config import Settings
from .logging_cfg import logger

# グローバル設定とクライアント
settings = Settings()
client = WebClient(token=settings.slack_token)

# レート制御用のグローバル変数
_last_call_ts = 0.0


def _respect_interval() -> None:
    """API呼び出し間隔を守る"""
    global _last_call_ts
    elapsed = time.perf_counter() - _last_call_ts
    if elapsed < settings.min_interval_sec:
        sleep_time = settings.min_interval_sec - elapsed
        time.sleep(sleep_time)
    _last_call_ts = time.perf_counter()


def search_messages_safe(query: str) -> int:
    """
    メッセージ検索を安全に実行（429リトライ付き）

    Args:
        query: 検索クエリ

    Returns:
        検索結果の総件数（429リトライ失敗時は0）
    """
    for attempt in range(1, settings.max_retry + 1):
        _respect_interval()

        try:
            logger.debug(f"Searching messages: {query}")
            resp = client.search_messages(query=query, count=1)
            messages = resp.get("messages") if resp else None
            if messages:
                total = messages.get("total", 0)
            else:
                total = 0
            logger.debug(f"Found {total} messages for query: {query}")
            return total

        except SlackApiError as e:
            if e.response.status_code == 429:
                retry_after = int(e.response.headers.get("Retry-After", "1"))
                retry_sec = retry_after + 1  # バッファとして1秒追加
                logger.warning(
                    f"Rate limited (429). Sleeping {retry_sec}s "
                    f"(attempt {attempt}/{settings.max_retry})"
                )
                time.sleep(retry_sec)
                continue
            else:
                logger.error(f"Slack API error: {e}")
                raise

    logger.error(f"Give up query after {settings.max_retry} retries: {query}")
    return 0


def get_custom_emojis() -> List[Dict[str, Any]]:
    """
    カスタム絵文字一覧を取得（429リトライ付き）

    Returns:
        カスタム絵文字のリスト（429リトライ失敗時は空リスト）
    """
    for attempt in range(1, settings.max_retry + 1):
        _respect_interval()

        try:
            logger.debug("Fetching custom emojis")
            resp = client.emoji_list()

            if not resp["ok"]:
                raise SlackApiError(
                    f"API error: {resp.get('error', 'Unknown error')}", resp
                )

            emojis = resp.get("emoji")
            if emojis:
                logger.info(f"Found {len(emojis)} custom emojis")
                return [{"name": name, "url": url} for name, url in emojis.items()]
            else:
                logger.info("No custom emojis found")
                return []

        except SlackApiError as e:
            if e.response.status_code == 429:
                retry_after = int(e.response.headers.get("Retry-After", "1"))
                retry_sec = retry_after + 1
                logger.warning(
                    f"Rate limited (429). Sleeping {retry_sec}s "
                    f"(attempt {attempt}/{settings.max_retry})"
                )
                time.sleep(retry_sec)
                continue
            else:
                logger.error(f"Slack API error: {e}")
                raise

    logger.error(f"Give up custom emoji fetch after {settings.max_retry} retries")
    return []


def get_workspace_info() -> Optional[Dict[str, Any]]:
    """
    ワークスペース情報を取得（429リトライ付き）

    Returns:
        ワークスペース情報（失敗時はNone）
    """
    for attempt in range(1, settings.max_retry + 1):
        _respect_interval()

        try:
            logger.debug("Fetching workspace info")
            resp = client.team_info()

            if not resp["ok"]:
                raise SlackApiError(
                    f"API error: {resp.get('error', 'Unknown error')}", resp
                )

            team_info = resp.get("team")
            if team_info:
                logger.debug(f"Workspace: {team_info.get('name', 'Unknown')}")
                return team_info
            else:
                logger.warning("No team info found")
                return {}

        except SlackApiError as e:
            if e.response.status_code == 429:
                retry_after = int(e.response.headers.get("Retry-After", "1"))
                retry_sec = retry_after + 1
                logger.warning(
                    f"Rate limited (429). Sleeping {retry_sec}s "
                    f"(attempt {attempt}/{settings.max_retry})"
                )
                time.sleep(retry_sec)
                continue
            else:
                logger.error(f"Slack API error: {e}")
                break

    logger.warning("Failed to get workspace info")
    return None