"""絵文字ローダーモジュール"""

import emoji
from typing import List, Set
from .slack_client import get_custom_emojis
from .logging_cfg import logger


def get_standard_emojis() -> List[str]:
    """
    標準絵文字の一覧を取得する

    Returns:
        標準絵文字名のリスト（:を除いた形式）
    """
    try:
        # emoji パッケージから標準絵文字を取得
        standard_emojis = []

        # Python emoji パッケージの絵文字データから取得
        emoji_data = emoji.EMOJI_DATA
        for emoji_char in emoji_data:
            emoji_name = emoji.demojize(emoji_char)
            # :name: 形式から name 部分を抽出
            if emoji_name.startswith(":") and emoji_name.endswith(":"):
                clean_name = emoji_name[1:-1]
                standard_emojis.append(clean_name)

        # 重複を除去してソート
        unique_emojis = sorted(list(set(standard_emojis)))
        logger.info(f"Loaded {len(unique_emojis)} standard emojis")
        return unique_emojis

    except Exception as e:
        logger.error(f"Failed to load standard emojis: {e}")
        return []


def get_custom_emoji_names() -> List[str]:
    """
    カスタム絵文字名の一覧を取得する

    Returns:
        カスタム絵文字名のリスト
    """
    try:
        custom_emoji_data = get_custom_emojis()
        custom_names = [emoji_info["name"] for emoji_info in custom_emoji_data]
        logger.info(f"Loaded {len(custom_names)} custom emojis")
        return sorted(custom_names)
    except Exception as e:
        logger.error(f"Failed to load custom emojis: {e}")
        return []


def load_emojis(
    include_standard: bool = True, include_custom: bool = True
) -> List[str]:
    """
    絵文字リストを読み込む

    Args:
        include_standard: 標準絵文字を含むかどうか
        include_custom: カスタム絵文字を含むかどうか

    Returns:
        絵文字名のリスト
    """
    all_emojis = []

    if include_standard:
        logger.info("Loading standard emojis...")
        standard_emojis = get_standard_emojis()
        all_emojis.extend(standard_emojis)

    if include_custom:
        logger.info("Loading custom emojis...")
        custom_emojis = get_custom_emoji_names()
        all_emojis.extend(custom_emojis)

    # 重複を除去（標準とカスタムで同名の場合）
    unique_emojis = list(dict.fromkeys(all_emojis))  # 順序を保持しつつ重複除去

    logger.info(f"Total emojis loaded: {len(unique_emojis)}")
    return unique_emojis


def filter_emojis(emoji_list: List[str], max_count: int) -> List[str]:
    """
    絵文字リストを指定された最大数に制限する

    Args:
        emoji_list: 絵文字名のリスト
        max_count: 最大絵文字数

    Returns:
        制限された絵文字名のリスト
    """
    if len(emoji_list) <= max_count:
        return emoji_list

    filtered = emoji_list[:max_count]
    logger.info(f"Emoji list filtered from {len(emoji_list)} to {len(filtered)}")
    return filtered


def validate_emoji_list(emoji_list: List[str]) -> List[str]:
    """
    絵文字リストを検証し、不正な名前を除去する

    Args:
        emoji_list: 絵文字名のリスト

    Returns:
        検証済みの絵文字名のリスト
    """
    valid_emojis = []

    for emoji_name in emoji_list:
        # 基本的な検証
        if not emoji_name or not isinstance(emoji_name, str):
            continue

        # 不正な文字を含まないかチェック
        if any(char in emoji_name for char in [" ", "\n", "\r", "\t"]):
            logger.warning(f"Skipping emoji with invalid characters: {emoji_name}")
            continue

        valid_emojis.append(emoji_name)

    removed_count = len(emoji_list) - len(valid_emojis)
    if removed_count > 0:
        logger.info(f"Removed {removed_count} invalid emoji names")

    return valid_emojis
