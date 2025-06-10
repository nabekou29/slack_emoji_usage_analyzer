"""クエリビルダーモジュール"""

from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from typing import List, Tuple

from .logging_cfg import logger


def generate_month_starts(months: int) -> List[date]:
    """
    指定された月数分の月初日を生成する

    Args:
        months: 対象月数

    Returns:
        月初日のリスト（新しい月から古い月の順）
    """
    month_starts = []
    current_date = datetime.now().date()

    for i in range(months):
        # i ヶ月前の月初を計算
        target_month = current_date - relativedelta(months=i)
        month_start = target_month.replace(day=1)
        month_starts.append(month_start)

    logger.debug(f"Generated {len(month_starts)} month periods")
    return month_starts


def generate_period_starts(total_months: int, interval_months: int = 1) -> List[date]:
    """
    指定された間隔で期間の開始日を生成する

    Args:
        total_months: 対象総期間（月数）
        interval_months: 集計間隔（月数）

    Returns:
        期間開始日のリスト（新しい期間から古い期間の順）
    """
    period_starts = []
    current_date = datetime.now().date()

    # 期間数を計算（切り上げ）
    period_count = (total_months + interval_months - 1) // interval_months

    for i in range(period_count):
        # i * interval_months ヶ月前の月初を計算
        months_back = i * interval_months
        if months_back >= total_months:
            break
        target_month = current_date - relativedelta(months=months_back)
        period_start = target_month.replace(day=1)
        period_starts.append(period_start)

    logger.debug(
        f"Generated {len(period_starts)} periods with {interval_months}-month intervals"
    )
    return period_starts


def build_monthly_queries(emoji_name: str, month_start: date) -> Tuple[str, str]:
    """
    指定された絵文字と月に対する検索クエリを構築する

    Args:
        emoji_name: 絵文字名（:なし）
        month_start: 対象月の開始日

    Returns:
        (テキスト検索クエリ, リアクション検索クエリ)のタプル
    """
    # 月の範囲を計算
    month_end = (month_start + relativedelta(months=1)) - relativedelta(days=1)

    # 日付文字列の作成
    start_str = month_start.strftime("%Y-%m-%d")
    end_str = month_end.strftime("%Y-%m-%d")

    # テキスト検索クエリ（メッセージ内での絵文字使用）
    text_query = f":{emoji_name}: after:{start_str} before:{end_str}"

    # リアクション検索クエリ（リアクションとしての絵文字使用）
    reaction_query = f"has::{emoji_name}: after:{start_str} before:{end_str}"

    logger.debug(f"Built queries for {emoji_name} in {start_str}")
    return text_query, reaction_query


def build_period_queries(
    emoji_name: str, period_start: date, interval_months: int
) -> Tuple[str, str]:
    """
    指定された絵文字と期間に対する検索クエリを構築する

    Args:
        emoji_name: 絵文字名（:なし）
        period_start: 対象期間の開始日
        interval_months: 期間の長さ（月数）

    Returns:
        (テキスト検索クエリ, リアクション検索クエリ)のタプル
    """
    # 期間の範囲を計算
    period_end = (period_start + relativedelta(months=interval_months)) - relativedelta(
        days=1
    )

    # 日付文字列の作成
    start_str = period_start.strftime("%Y-%m-%d")
    end_str = period_end.strftime("%Y-%m-%d")

    # テキスト検索クエリ（メッセージ内での絵文字使用）
    text_query = f":{emoji_name}: after:{start_str} before:{end_str}"

    # リアクション検索クエリ（リアクションとしての絵文字使用）
    reaction_query = f"has::{emoji_name}: after:{start_str} before:{end_str}"

    logger.debug(
        f"Built queries for {emoji_name} in {start_str} to {end_str} ({interval_months}M)"
    )
    return text_query, reaction_query


def validate_query(query: str) -> bool:
    """
    検索クエリの妥当性を検証する

    Args:
        query: 検索クエリ

    Returns:
        クエリが有効かどうか
    """
    if not query or not isinstance(query, str):
        return False

    # 基本的な長さチェック
    if len(query) > 1000:  # Slack APIの制限を考慮
        logger.warning(f"Query too long: {len(query)} characters")
        return False

    # 必須要素のチェック
    if ":" not in query:
        logger.warning(f"Query missing emoji pattern: {query}")
        return False

    return True


def escape_emoji_name(emoji_name: str) -> str:
    """
    絵文字名をクエリで安全に使用できるようエスケープする

    Args:
        emoji_name: 絵文字名

    Returns:
        エスケープされた絵文字名
    """
    # 特殊文字をエスケープ（必要に応じて拡張）
    escaped = emoji_name.replace('"', '\\"')
    return escaped


def build_test_queries(
    emoji_names: List[str], months: int = 1
) -> List[Tuple[str, str, str]]:
    """
    テスト用のクエリリストを構築する

    Args:
        emoji_names: テスト対象の絵文字名リスト
        months: テスト期間（月数）

    Returns:
        (絵文字名, テキストクエリ, リアクションクエリ)のタプルのリスト
    """
    test_queries = []
    month_starts = generate_month_starts(months)

    for emoji_name in emoji_names:
        for month_start in month_starts:
            text_query, reaction_query = build_monthly_queries(emoji_name, month_start)
            test_queries.append((emoji_name, text_query, reaction_query))

    logger.info(f"Built {len(test_queries)} test queries")
    return test_queries
